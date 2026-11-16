#include "UpperSerialDebug.h"

#include <string.h>

#define UPPER_SERIAL_MAGIC_0 ((uint8_t)'U')
#define UPPER_SERIAL_MAGIC_1 ((uint8_t)'S')
#define UPPER_SERIAL_MAGIC_2 ((uint8_t)'S')
#define UPPER_SERIAL_MAGIC_3 ((uint8_t)'V')
#define UPPER_SERIAL_HEADER_SIZE 12u
#define UPPER_SERIAL_CRC_SIZE 4u
#define UPPER_SERIAL_TLV_SIZE 3u
#define UPPER_SERIAL_TAG_STATUS 1u
#define UPPER_SERIAL_TAG_ODO 2u
#define UPPER_SERIAL_TAG_VEHICLE 3u
#define UPPER_SERIAL_TAG_RAW 4u
#define UPPER_SERIAL_TAG_PDC 5u
#define UPPER_SERIAL_TAG_POINT 6u
#define UPPER_SERIAL_TAG_LINE 7u
#define UPPER_SERIAL_TAG_SLOT 8u
#define UPPER_SERIAL_BLOCK_LIMIT 1024u
#define UPPER_SERIAL_PACKET_LIMIT 2048u

static UpperSerialWriteFn s_writer;
static void *s_writer_context;
static uint32_t s_sequence;
static int s_sending;
/* Fixed storage keeps the MCU task stack independent of packet capacity. */
static uint8_t s_packet[UPPER_SERIAL_PACKET_LIMIT];
static uint8_t s_body[UPPER_SERIAL_BLOCK_LIMIT];
typedef char UpperSerialFloatMustBe32Bits[(sizeof(float) == 4u) ? 1 : -1];

static void put_u16(uint8_t *dst, uint16_t value)
{
    dst[0] = (uint8_t)(value & 0xffu);
    dst[1] = (uint8_t)(value >> 8);
}

static void put_i16(uint8_t *dst, int16_t value)
{
    put_u16(dst, (uint16_t)value);
}

static void put_u32(uint8_t *dst, uint32_t value)
{
    dst[0] = (uint8_t)(value & 0xffu);
    dst[1] = (uint8_t)((value >> 8) & 0xffu);
    dst[2] = (uint8_t)((value >> 16) & 0xffu);
    dst[3] = (uint8_t)(value >> 24);
}

static void put_u64(uint8_t *dst, uint64_t value)
{
    uint8_t i;
    for (i = 0u; i < 8u; ++i) {
        dst[i] = (uint8_t)(value >> (8u * i));
    }
}

static void put_f32(uint8_t *dst, float value)
{
    uint32_t bits = 0u;
    memcpy(&bits, &value, sizeof(bits));
    put_u32(dst, bits);
}

static int append_tlv(uint8_t *payload, uint16_t *payload_size, uint8_t tag,
                      const uint8_t *body, uint16_t body_size)
{
    uint16_t next = (uint16_t)(*payload_size + UPPER_SERIAL_TLV_SIZE + body_size);
    if (next < *payload_size || next > UPPER_SERIAL_PACKET_LIMIT - UPPER_SERIAL_HEADER_SIZE - UPPER_SERIAL_CRC_SIZE) {
        return UPPER_SERIAL_ERR_TOO_LARGE;
    }
    payload[*payload_size] = tag;
    put_u16(payload + *payload_size + 1u, body_size);
    memcpy(payload + *payload_size + UPPER_SERIAL_TLV_SIZE, body, body_size);
    *payload_size = next;
    return UPPER_SERIAL_OK;
}

static uint16_t encode_status(uint8_t *body, const UpperSerialStatus *status)
{
    body[0] = status->gear;
    put_u16(body + 1u, status->temperature);
    put_f32(body + 3u, status->speed);
    put_u64(body + 7u, status->timestamp);
    return 15u;
}

static uint16_t encode_odo(uint8_t *body, const UpperSerialOdo *odo)
{
    put_f32(body, odo->x);
    put_f32(body + 4u, odo->y);
    put_f32(body + 8u, odo->angle);
    return 12u;
}

static uint16_t encode_vehicle(uint8_t *body, const UpperSerialVehicle *vehicle)
{
    uint8_t i;
    put_u16(body, vehicle->length);
    put_u16(body + 2u, vehicle->width);
    for (i = 0u; i < 24u; ++i) {
        put_i16(body + 4u + 2u * i, vehicle->sensor_xy[i]);
    }
    return 52u;
}

static uint16_t encode_raw(uint8_t *body, const UpperSerialFrame *frame)
{
    uint8_t i;
    uint8_t *cursor = body;
    put_u16(cursor, frame->same_frequency_front_count);
    put_u16(cursor + 2u, frame->same_frequency_rear_count);
    cursor[4] = frame->same_frequency_front_flag;
    cursor[5] = frame->same_frequency_rear_flag;
    cursor[6] = UPPER_SERIAL_SENSOR_COUNT;
    cursor += 7u;
    for (i = 0u; i < UPPER_SERIAL_SENSOR_COUNT; ++i) {
        const UpperSerialRaw *raw = &frame->raw[i];
        cursor[0] = raw->mode;
        put_u16(cursor + 1u, raw->de);
        put_u16(cursor + 3u, raw->de_peak);
        put_u16(cursor + 5u, raw->de_width);
        put_u16(cursor + 7u, raw->ce_left);
        put_u16(cursor + 9u, raw->ce_left_peak);
        put_u16(cursor + 11u, raw->ce_left_width);
        put_u16(cursor + 13u, raw->ce_right);
        put_u16(cursor + 15u, raw->ce_right_peak);
        put_u16(cursor + 17u, raw->ce_right_width);
        cursor += 19u;
    }
    return (uint16_t)(7u + 19u * UPPER_SERIAL_SENSOR_COUNT);
}

static uint16_t encode_pdc(uint8_t *body, const UpperSerialFrame *frame)
{
    uint8_t i;
    uint8_t *cursor = body;
    cursor[0] = frame->pdc_status;
    cursor[1] = frame->pdc_front_status;
    cursor[2] = frame->pdc_rear_status;
    cursor[3] = UPPER_SERIAL_SENSOR_COUNT;
    cursor += 4u;
    for (i = 0u; i < UPPER_SERIAL_SENSOR_COUNT; ++i) {
        put_u16(cursor, frame->pdc[i].distance);
        cursor[2] = frame->pdc[i].range;
        cursor[3] = frame->pdc[i].fault;
        cursor += 4u;
    }
    return (uint16_t)(4u + 4u * UPPER_SERIAL_SENSOR_COUNT);
}

static uint16_t encode_points(uint8_t *body, const UpperSerialFrame *frame)
{
    uint16_t i;
    uint8_t *cursor = body;
    put_u16(cursor, frame->point_count);
    cursor += 2u;
    for (i = 0u; i < frame->point_count; ++i) {
        const UpperSerialPoint *point = &frame->points[i];
        put_u16(cursor, point->object_id);
        put_i16(cursor + 2u, point->x);
        put_i16(cursor + 4u, point->y);
        cursor[6] = point->height;
        cursor[7] = point->tx_index;
        cursor[8] = point->rx_index;
        cursor += 9u;
    }
    return (uint16_t)(2u + 9u * frame->point_count);
}

static uint16_t encode_lines(uint8_t *body, const UpperSerialFrame *frame)
{
    uint16_t i;
    uint8_t *cursor = body;
    put_u16(cursor, frame->line_count);
    cursor += 2u;
    for (i = 0u; i < frame->line_count; ++i) {
        const UpperSerialLine *line = &frame->lines[i];
        cursor[0] = line->number;
        cursor[1] = line->height;
        cursor[2] = line->object_type;
        put_i16(cursor + 3u, line->start_x);
        put_i16(cursor + 5u, line->start_y);
        put_i16(cursor + 7u, line->end_x);
        put_i16(cursor + 9u, line->end_y);
        put_u16(cursor + 11u, line->distance);
        cursor += 13u;
    }
    return (uint16_t)(2u + 13u * frame->line_count);
}

static uint16_t encode_slot(uint8_t *body, const UpperSerialSlot *slot)
{
    uint8_t i;
    put_u64(body, slot->timestamp);
    body[8] = slot->id;
    body[9] = slot->type;
    put_u16(body + 10u, slot->width);
    put_u16(body + 12u, slot->depth);
    put_i16(body + 14u, slot->point_xy[0]);
    put_i16(body + 16u, slot->point_xy[1]);
    body[18] = slot->point_a_type;
    for (i = 2u; i < 12u; ++i) {
        put_i16(body + 19u + 2u * (i - 2u), slot->point_xy[i]);
    }
    body[39] = slot->point_f_type;
    return 40u;
}

void UpperSerialDebug_SetWriter(UpperSerialWriteFn writer, void *context)
{
    s_writer = writer;
    s_writer_context = context;
}

int UpperSerialDebug_HasWriter(void)
{
    return s_writer != NULL;
}

uint32_t UpperSerialDebug_NextSequence(void)
{
    ++s_sequence;
    return s_sequence;
}

uint32_t UpperSerialDebug_Crc32(const uint8_t *data, uint16_t size)
{
    uint32_t crc = 0xffffffffu;
    uint16_t i;
    for (i = 0u; i < size; ++i) {
        uint8_t bit;
        crc ^= data[i];
        for (bit = 0u; bit < 8u; ++bit) {
            crc = (crc >> 1u) ^ (0xedb88320u & (uint32_t)-(int32_t)(crc & 1u));
        }
    }
    return ~crc;
}

int UpperSerialDebug_SendFrame(const UpperSerialFrame *frame)
{
    uint8_t *packet = s_packet;
    uint8_t *body = s_body;
    uint16_t payload_size = 0u;
    uint16_t body_size;
    uint16_t total_size;
    uint32_t sequence;
    int result;
    if (frame == NULL || s_writer == NULL || frame->point_count > UPPER_SERIAL_POINT_MAX ||
        frame->line_count > UPPER_SERIAL_LINE_MAX || frame->slot_side_capacity < 3u ||
        frame->slot_side_capacity > UPPER_SERIAL_SLOT_SIDE_MAX ||
        frame->slot_left_count > frame->slot_side_capacity ||
        frame->slot_right_count > frame->slot_side_capacity) {
        return frame == NULL ? UPPER_SERIAL_ERR_ARGUMENT :
               (s_writer == NULL ? UPPER_SERIAL_ERR_NO_WRITER : UPPER_SERIAL_ERR_ARGUMENT);
    }
    if (s_sending) return UPPER_SERIAL_ERR_BUSY;
    body_size = encode_status(body, &frame->status);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_STATUS, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_odo(body, &frame->odo);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_ODO, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_vehicle(body, &frame->vehicle);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_VEHICLE, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_raw(body, frame);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_RAW, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_pdc(body, frame);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_PDC, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_points(body, frame);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_POINT, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    body_size = encode_lines(body, frame);
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_LINE, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    {
        uint8_t i;
        uint8_t *cursor = body;
        cursor[0] = frame->slot_status;
        cursor[1] = frame->slot_left_count;
        cursor[2] = frame->slot_right_count;
        cursor[3] = frame->slot_side_capacity;
        cursor += 4u;
        for (i = 0u; i < (uint8_t)(2u * frame->slot_side_capacity); ++i) {
            encode_slot(cursor, &frame->slots[i]);
            cursor += 40u;
        }
        body_size = (uint16_t)(4u + 40u * 2u * frame->slot_side_capacity);
    }
    result = append_tlv(packet + UPPER_SERIAL_HEADER_SIZE, &payload_size,
                         UPPER_SERIAL_TAG_SLOT, body, body_size);
    if (result != UPPER_SERIAL_OK) return result;
    sequence = frame->sequence != 0u ? frame->sequence : UpperSerialDebug_NextSequence();
    packet[0] = UPPER_SERIAL_MAGIC_0;
    packet[1] = UPPER_SERIAL_MAGIC_1;
    packet[2] = UPPER_SERIAL_MAGIC_2;
    packet[3] = UPPER_SERIAL_MAGIC_3;
    packet[4] = UPPER_SERIAL_VERSION;
    packet[5] = 0u;
    put_u16(packet + 6u, payload_size);
    put_u32(packet + 8u, sequence);
    total_size = (uint16_t)(UPPER_SERIAL_HEADER_SIZE + payload_size);
    put_u32(packet + total_size, UpperSerialDebug_Crc32(packet, total_size));
    total_size = (uint16_t)(total_size + UPPER_SERIAL_CRC_SIZE);
    s_sending = 1;
    result = s_writer(packet, total_size, s_writer_context);
    s_sending = 0;
    return result == 0 ? UPPER_SERIAL_OK : UPPER_SERIAL_ERR_WRITE;
}

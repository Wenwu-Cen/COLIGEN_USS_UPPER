#ifndef UPPER_SERIAL_DEBUG_H
#define UPPER_SERIAL_DEBUG_H

#include <stdint.h>

/*
 * LAUTERBACH_UPPER_DEBUG variables are copied into these wire structs by the
 * firmware glue. The wire encoder never sends C padding, so the same bytes
 * are decoded on Windows, Linux and the target MCU.
 */
#define UPPER_SERIAL_POINT_MAX 80u
#define UPPER_SERIAL_LINE_MAX 20u
#define UPPER_SERIAL_SENSOR_COUNT 12u
#define UPPER_SERIAL_SLOT_SIDE_MAX 4u
#define UPPER_SERIAL_SLOT_MAX (2u * UPPER_SERIAL_SLOT_SIDE_MAX)
#define UPPER_SERIAL_VERSION 1u
#define UPPER_SERIAL_MAX_PAYLOAD 8192u

#define UPPER_SERIAL_OK 0
#define UPPER_SERIAL_ERR_ARGUMENT -1
#define UPPER_SERIAL_ERR_NO_WRITER -2
#define UPPER_SERIAL_ERR_TOO_LARGE -3
#define UPPER_SERIAL_ERR_WRITE -4
#define UPPER_SERIAL_ERR_BUSY -5

typedef int (*UpperSerialWriteFn)(const uint8_t *data, uint16_t size, void *context);

typedef struct {
    uint8_t gear;
    uint16_t temperature;
    float speed;
    uint64_t timestamp;
} UpperSerialStatus;

typedef struct {
    float x;
    float y;
    float angle;
} UpperSerialOdo;

typedef struct {
    uint16_t length;
    uint16_t width;
    int16_t sensor_xy[24]; /* RRS .. FLS, X/Y pairs, millimetres */
} UpperSerialVehicle;

typedef struct {
    uint8_t mode;
    uint16_t de;
    uint16_t de_peak;
    uint16_t de_width;
    uint16_t ce_left;
    uint16_t ce_left_peak;
    uint16_t ce_left_width;
    uint16_t ce_right;
    uint16_t ce_right_peak;
    uint16_t ce_right_width;
} UpperSerialRaw;

typedef struct {
    uint16_t distance;
    uint8_t range;
    uint8_t fault;
} UpperSerialPdc;

typedef struct {
    uint16_t object_id;
    int16_t x;
    int16_t y;
    uint8_t height;
    uint8_t tx_index;
    uint8_t rx_index;
} UpperSerialPoint;

typedef struct {
    uint8_t number;
    uint8_t height;
    uint8_t object_type;
    int16_t start_x;
    int16_t start_y;
    int16_t end_x;
    int16_t end_y;
    uint16_t distance;
} UpperSerialLine;

typedef struct {
    uint64_t timestamp;
    uint8_t id;
    uint8_t type;
    uint16_t width;
    uint16_t depth;
    int16_t point_xy[12]; /* A..F X/Y pairs */
    uint8_t point_a_type;
    uint8_t point_f_type;
} UpperSerialSlot;

typedef struct {
    uint32_t sequence;
    UpperSerialStatus status;
    UpperSerialOdo odo;
    UpperSerialVehicle vehicle;
    uint16_t same_frequency_front_count;
    uint16_t same_frequency_rear_count;
    uint8_t same_frequency_front_flag;
    uint8_t same_frequency_rear_flag;
    UpperSerialRaw raw[UPPER_SERIAL_SENSOR_COUNT];
    uint8_t pdc_status;
    uint8_t pdc_front_status;
    uint8_t pdc_rear_status;
    UpperSerialPdc pdc[UPPER_SERIAL_SENSOR_COUNT];
    UpperSerialPoint points[UPPER_SERIAL_POINT_MAX];
    uint16_t point_count;
    UpperSerialLine lines[UPPER_SERIAL_LINE_MAX];
    uint16_t line_count;
    uint8_t slot_status;
    uint8_t slot_left_count;
    uint8_t slot_right_count;
    uint8_t slot_side_capacity; /* 3 for sf_Upper_SlotOutSignal[3], 4 for 8 slots */
    UpperSerialSlot slots[UPPER_SERIAL_SLOT_MAX]; /* left side, then right side */
} UpperSerialFrame;

/* Single producer task. Writer must copy/enqueue the full frame before returning. */
void UpperSerialDebug_SetWriter(UpperSerialWriteFn writer, void *context);
int UpperSerialDebug_HasWriter(void);
uint32_t UpperSerialDebug_NextSequence(void);
uint32_t UpperSerialDebug_Crc32(const uint8_t *data, uint16_t size);
int UpperSerialDebug_SendFrame(const UpperSerialFrame *frame);
/* UpperSerialVariables.c; requires LAUTERBACH_UPPER_DEBUG and native sf_Upper variables. */
int UpperSerialDebug_SendVariables(void);

/* Call this after OutputSignalRead_* completed one coherent debug snapshot. */
static inline int UpperSerialDebug_Publish(const UpperSerialFrame *frame)
{
    return UpperSerialDebug_SendFrame(frame);
}

#endif /* UPPER_SERIAL_DEBUG_H */

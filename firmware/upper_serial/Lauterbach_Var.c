#include "Lauterbach_Var.h"
#include "UpperSerialDebug.h"
#include <string.h>

#ifdef LAUTERBACH_UPPER_DEBUG
/* Replace this file with the target's existing definitions when porting. */
Upper_PointOutSignal sf_Upper_PointOutSignal[80];
Upper_LineOutSignal sf_Upper_LineOutSignal[20];
Upper_StatusOutSignal sf_Upper_StatusOutSignal;
Upper_OdoOutSignal sf_Upper_OdoOutSignal;
Upper_VehicleOutSignal sf_Upper_VehicleOutSignal;
Upper_RawDataOutSignal sf_Upper_RawDataOutSignal;
Upper_PDCOutSignal sf_Upper_PDCOutSignal;
Upper_SlotOutSignal sf_Upper_SlotOutSignal;

#endif

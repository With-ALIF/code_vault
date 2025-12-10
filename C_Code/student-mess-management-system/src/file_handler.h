#ifndef FILE_HANDLER_H
#define FILE_HANDLER_H

#include "student.h"

void load_students(Student students[], int *count);
void save_students(Student students[], int count);
void save_meal_log(const char *roll_no, const char *meal_type, const char *action);

#endif

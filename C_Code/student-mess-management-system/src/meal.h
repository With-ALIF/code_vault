#ifndef MEAL_H
#define MEAL_H

#include "student.h"

#define MEAL_BREAKFAST 1
#define MEAL_LUNCH 2
#define MEAL_DINNER 4

#define COST_BREAKFAST 20.0
#define COST_LUNCH 35.0
#define COST_DINNER 45.0

void display_menu(void);
void book_meal(Student *s);
void cancel_meal(Student *s);
void check_meal_status(const Student *s);

#endif 
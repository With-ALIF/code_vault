#ifndef BILLING_H
#define BILLING_H

#include "student.h"

double calculate_monthly_bill(const Student *s);
double generate_rebate(const Student *s, double bill_amount);
void deduct_balance(Student *s, double amount);

#endif
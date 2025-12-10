#include <stdio.h>
#include "billing.h"
#include "meal.h"
#include "student.h"

double calculate_monthly_bill(const Student *s) {
    if (s == NULL) return 0.0;

    double total = 0.0;
    for (int i = 0; i < MAX_DAYS; ++i) {
        int mask = s->meals_consumed[i];

        if (mask & MEAL_BREAKFAST)
            total += COST_BREAKFAST;
        if (mask & MEAL_LUNCH)
            total += COST_LUNCH;
        if (mask & MEAL_DINNER)
            total += COST_DINNER;
    }
    return total;
}

double generate_rebate(const Student *s, double bill_amount) {
    if (s == NULL) return 0.0;

    int meal_count = 0;
    for (int i = 0; i < MAX_DAYS; ++i) {
        int mask = s->meals_consumed[i];
        if (mask & MEAL_BREAKFAST)
            meal_count++;
        if (mask & MEAL_LUNCH)
            meal_count++;
        if (mask & MEAL_DINNER)
            meal_count++;
    }

    if (meal_count < 30) {
        return bill_amount * 0.05;
    }
    return 0.0;
}

void deduct_balance(Student *s, double amount) {
    if (s == NULL) return;

    if (s->current_balance < amount) {
        printf("Insufficient balance. Please deposit more funds.\n");
        return;
    }

    s->current_balance -= amount;
    printf("Amount %.2f deducted. New balance: %.2f\n", amount, s->current_balance);
}

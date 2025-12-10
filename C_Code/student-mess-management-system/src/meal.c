#include <stdio.h>
#include <time.h>
#include "meal.h"
#include "file_handler.h"

static void clear_input_buffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF) {}
}

static int choose_meal_type(void) {
    int choice;
    printf("\nSelect Meal Type:\n");
    printf("1. Breakfast\n");
    printf("2. Lunch\n");
    printf("3. Dinner\n");
    printf("Choice: ");
    scanf("%d", &choice);
    clear_input_buffer();

    switch (choice) {
        case 1: return MEAL_BREAKFAST;
        case 2: return MEAL_LUNCH;
        case 3: return MEAL_DINNER;
        default:
            printf("Invalid choice\n");
            return 0;
    }
}

static int choose_day(void) {
    int day;
    printf("Enter day of month (1 - %d):", MAX_DAYS);
    scanf("%d", &day);
    clear_input_buffer();

    if (day < 1 || day > MAX_DAYS) {
        printf("Invalid day.\n");
        return -1;
    }
    return day - 1;
}

void display_menu(void) {
    printf("\n--- Today's Menu---\n");
    printf("Breakfast: Bread, Egg, Tea (%.2f)\n", COST_BREAKFAST);
    printf("Lunch: Rice, Dal, Chicken (%.2f)\n", COST_LUNCH);
    printf("Dinner: Rice, Fish, Curry (%.2f)\n", COST_DINNER);
}

void book_meal(Student *s) {
    if (s == NULL) {
        printf("No student logged in.\n");
        return;
    }

    int meal_type = choose_meal_type();
    if (meal_type == 0)
        return;

    int day_index = choose_day();
    if (day_index < 0)
        return;

    if (s->meals_consumed[day_index] & meal_type) {
        printf("You have already booked this meal for that day.\n");
        return;
    }

    s->meals_consumed[day_index] |= meal_type;

    if (meal_type == MEAL_BREAKFAST)
        save_meal_log(s->roll_no, "Breakfast", "Booked");
    else if (meal_type == MEAL_LUNCH)
        save_meal_log(s->roll_no, "Lunch", "Booked");
    else if (meal_type == MEAL_DINNER)
        save_meal_log(s->roll_no, "Dinner", "Booked");

    printf("Meal booked successfully\n");
}

void cancel_meal(Student *s) {
    if (s == NULL) {
        printf("No student logged in.\n");
        return;
    }

    int meal_type = choose_meal_type();
    if (meal_type == 0)
        return;

    int day_index = choose_day();
    if (day_index < 0)
        return;

    if (meal_type == MEAL_DINNER) {
        time_t t = time(NULL);
        struct tm *now = localtime(&t);
        if (now && now->tm_hour >= 16) {
            printf("You cannot cancel dinner after 4PM.\n");
            return;
        }
    }

    if (!(s->meals_consumed[day_index] & meal_type)) {
        printf("No such meal booking found for that day.\n");
        return;
    }

    s->meals_consumed[day_index] &= ~meal_type;

    if (meal_type == MEAL_BREAKFAST)
        save_meal_log(s->roll_no, "Breakfast", "Cancel");
    else if (meal_type == MEAL_LUNCH)
        save_meal_log(s->roll_no, "Lunch", "Cancel");
    else if (meal_type == MEAL_DINNER)
        save_meal_log(s->roll_no, "Dinner", "Cancel");

    printf("Meal cancelled successfully.\n");
}

void check_meal_status(const Student *s) {
    if (s == NULL) {
        printf("No student logged in.\n");
        return;
    }

    printf("\n--- Meal status for %s ---\n", s->name);

    for (int i = 0; i < MAX_DAYS; ++i) {
        int mask = s->meals_consumed[i];
        if (mask == 0)
            continue;

        printf("Day %2d: ", i + 1);
        if (mask & MEAL_BREAKFAST)
            printf("[Breakfast] ");
        if (mask & MEAL_LUNCH)
            printf("[Lunch] ");
        if (mask & MEAL_DINNER)
            printf("[Dinner] ");
        printf("\n");
    }
}

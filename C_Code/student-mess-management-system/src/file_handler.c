#include <stdio.h>
#include <string.h>
#include "file_handler.h"

#define STUDENT_FILE "students.txt"
#define MEAL_LOG_FILE "meal_log.txt"

void load_students(Student students[], int *count) {
    *count = 0;
    FILE *fp = fopen(STUDENT_FILE, "r");
    if (!fp) {
        return;
    }

    while (*count < MAX_STUDENTS) {
        Student s;
        int read;

        read = fscanf(fp, "%14s %49s %d %lf",
                      s.roll_no,
                      s.name,
                      &s.room_number,
                      &s.current_balance);

        if (read != 4)
            break;

        for (int i = 0; i < MAX_DAYS; ++i) {
            s.meals_consumed[i] = 0;
        }

        students[(*count)++] = s;
    }

    fclose(fp);
}

void save_students(Student students[], int count) {
    FILE *fp = fopen(STUDENT_FILE, "w");
    if (!fp) {
        printf("Error: Could not open file for writing.\n");
        return;
    }

    for (int i = 0; i < count; ++i) {
        fprintf(fp, "%s %s %d %.2f\n",
                students[i].roll_no,
                students[i].name,
                students[i].room_number,
                students[i].current_balance);
    }

    fclose(fp);
}

void save_meal_log(const char *roll_no, const char *meal_type, const char *action) {
    FILE *fp = fopen(MEAL_LOG_FILE, "a");
    if (!fp) {
        printf("Error: could not open meal log file.\n");
        return;
    }

    fprintf(fp, "%s %s %s\n", roll_no, meal_type, action);

    fclose(fp);   
}

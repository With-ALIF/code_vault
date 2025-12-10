#include <stdio.h>
#include <string.h>
#include "student.h"
#include "file_handler.h"

Student students[MAX_STUDENTS];
int student_count = 0;

static void clear_input_buffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF) {}
}

void init_students(void) {
    load_students(students, &student_count);
}

void persist_students(void) {
    save_students(students, student_count);
}

Student* find_student_by_roll(const char *roll_no) {
    for (int i = 0; i < student_count; ++i) {
        if (strcmp(students[i].roll_no, roll_no) == 0) {
            return &students[i];
        }
    }
    return NULL;
}

void register_student(void) {
    if (student_count >= MAX_STUDENTS) {
        printf("Cannot register more students. Limit reached.\n");
        return;
    }

    Student s;
    memset(&s, 0, sizeof(Student));

    printf("\n--- Register New Student ---\n");
    printf("Roll No: ");
    scanf("%14s", s.roll_no);
    clear_input_buffer();

    if (find_student_by_roll(s.roll_no) != NULL) {
        printf("A student with this roll number already exists.\n");
        return;
    }

    printf("Name: ");
    fgets(s.name, sizeof(s.name), stdin);
    size_t len = strlen(s.name);
    if (len > 0 && s.name[len - 1] == '\n') {
        s.name[len - 1] = '\0';
    }

    printf("Room Number: ");
    scanf("%d", &s.room_number);
    clear_input_buffer();

    printf("Initial Deposit Balance: ");
    scanf("%lf", &s.current_balance);
    clear_input_buffer();

    for (int i = 0; i < MAX_DAYS; ++i) {
        s.meals_consumed[i] = 0;
    }

    students[student_count++] = s;
    persist_students();
    printf("Student registered successfully.\n");
}

void view_profile(const Student *s) {
    if (s == NULL) {
        printf("No student selected.\n");
        return;
    }

    printf("\n--- Student Profile ---\n");
    printf("Roll No: %s\n", s->roll_no);
    printf("Name: %s\n", s->name);
    printf("Room Number: %d\n", s->room_number);
    printf("Current Balance: %.2f\n", s->current_balance);
}

void update_room_number(Student *s) {
    if (s == NULL) {
        printf("No student selected.\n");
        return;
    }

    int new_room;
    printf("Enter new room number: ");
    scanf("%d", &new_room);
    clear_input_buffer();

    s->room_number = new_room;
    persist_students();
    printf("Room number updated successfully.\n");
}

void list_all_students(void) {
    printf("\n--- All Registered Students ---\n");

    if (student_count == 0) {
        printf("No students registered yet.\n");
        return;
    }

    for (int i = 0; i < student_count; ++i) {
        printf("%d) %s | %s | Room %d | Balance: %.2f\n",
               i + 1,
               students[i].roll_no,
               students[i].name,
               students[i].room_number,
               students[i].current_balance);
    }
}

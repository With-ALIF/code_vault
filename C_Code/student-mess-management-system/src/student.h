#ifndef STUDENT_H
#define STUDENT_H

#define MAX_STUDENTS 100
#define MAX_DAYS 30

typedef struct {
    char roll_no[15];
    char name[50];
    int room_number;
    double current_balance;
    int meals_consumed[MAX_DAYS];
} Student;

extern Student students[MAX_STUDENTS];
void init_students(void);
void persist_students(void);
void register_student(void);
Student* find_student_by_roll(const char *roll_no);
void view_profile(const Student *s);
void update_room_number(Student *s);

void list_all_students(void);

#endif
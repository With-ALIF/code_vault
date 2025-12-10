// cd ~/coding/Runnig\ Project/alif/spl-project/src

#include <stdio.h>
#include <string.h>
#include "auth.h"
#include "student.h"

static void clear_input_buffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF) {}
}

#define ADMIN_USERNAME "admin"
#define ADMIN_PASSWORD "1234"

int admin_login(void) {
    char username[50];
    char password[50];

    printf("\n--- Admin Login ---\n");
    printf("Username: ");
    scanf("%49s", username);
    printf("Password: ");
    scanf("%49s", password);
    clear_input_buffer();

    if (strcmp(username, ADMIN_USERNAME) == 0 && strcmp(password, ADMIN_PASSWORD) == 0) {
        printf("Admin login successful.\n");
        return 1;
    } else {
        printf("Invalid admin credentials.\n");
        return 0;
    }
}

Student* student_login(void) {
    char roll[15];
    printf("\n--- Student Login ---\n");
    printf("Enter Roll no: ");
    scanf("%14s", roll);
    clear_input_buffer();

    Student *s = find_student_by_roll(roll);
    if (s == NULL) {
        printf("Student not found. Please register first.\n");
        return NULL;
    }
    printf("Welcome, %s (Room %d)\n", s->name, s->room_number);
    return s;
}

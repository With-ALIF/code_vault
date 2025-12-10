#include <stdio.h>
#include <stdlib.h>
#include "auth.h"
#include "student.h"
#include "meal.h"
#include "billing.h"

static void clear_input_buffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF) {}
}

static void admin_menu(void) {
    int choice;
    do {
        printf("\n=== Admin Menu ===\n");
        printf("1. Register Student\n");
        printf("2. List All Students\n");
        printf("3. Display Mess Menu\n");
        printf("4. Back to Main Menu\n");
        printf("Choice: ");
        scanf("%d", &choice);
        clear_input_buffer();

        switch (choice) {
            case 1:
                register_student();
                break;
            case 2:
                list_all_students();
                break;
            case 3:
                display_menu();
                break;
            case 4:
                printf("Returning to main menu...\n");
                break;
            default:
                printf("Invalid choice.\n");
        }
    } while (choice != 4);
}

static void student_menu(Student *s) {
    int choice;
    do {
        printf("\n=== Student Menu (%s) ===\n", s->name);
        printf("1. View Profile\n");
        printf("2. Update Room Number\n");
        printf("3. Display Mess Menu\n");
        printf("4. Book Meal\n");
        printf("5. Cancel Meal\n");
        printf("6. Check Meal Status\n");
        printf("7. Generate Monthly Bill & Deduct\n");
        printf("8. Logout\n");
        printf("Choice: ");
        scanf("%d", &choice);
        clear_input_buffer();

        switch (choice) {
            case 1:
                view_profile(s);
                break;
            case 2:
                update_room_number(s);
                break;
            case 3:
                display_menu();
                break;
            case 4:
                book_meal(s);
                break;
            case 5:
                cancel_meal(s);
                break;
            case 6:
                check_meal_status(s);
                break;
            case 7: {
                double bill = calculate_monthly_bill(s);
                double rebate = generate_rebate(s, bill);
                double final_amount = bill - rebate;

                printf("\n--- Billing Summary ---\n");
                printf("Gross Bill : %.2f\n", bill);
                printf("Rebate     : %.2f\n", rebate);
                printf("Net Payable: %.2f\n", final_amount);

                deduct_balance(s, final_amount);
                break;
            }
            case 8:
                printf("Logging out...\n");
                break;
            default:
                printf("Invalid choice.\n");
        }
    } while (choice != 8);
}

int main(void) {
    int choice;
    init_students();

    while (1) {
        printf("\n=== Student Hall Mess Management System ===\n");
        printf("1. Admin Login\n");
        printf("2. Student Login\n");
        printf("3. Exit\n");
        printf("Choice: ");
        if (scanf("%d", &choice) != 1) {
            clear_input_buffer();
            continue;
        }
        clear_input_buffer();

        switch (choice) {
            case 1:
                if (admin_login()) {
                    admin_menu();
                }
                break;
            case 2: {
                Student *s = student_login();
                if (s != NULL) {
                    student_menu(s);
                }
                break;
            }
            case 3:
                printf("Exiting... Saving data.\n");
                persist_students();
                exit(0);
            default:
                printf("Invalid choice.\n");
        }
    }

    return 0;
}

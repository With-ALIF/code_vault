<h1 align="center" style="color:#1565C0; font-size: 42px;">
  📘 Student Hall Mess Management & Food Registration System
</h1>

<h3 align="center" style="color:#00897B; font-size: 22px;">
  ✨ A Demonstration of Modular Programming in C ✨
</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Language-C-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Paradigm-Modular_Programming-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Build-gcc%20%2B%20Makefile-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Usage-Academic_Project-purple?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-Linux%2FUnix-lightgrey?style=for-the-badge" />
</p>

---

<h2 style="color:#D81B60; font-size: 28px;">📖 Overview</h2>

The **Student Hall Mess Management System** is a modular C-based application designed to digitalize and streamline university mess administration.  
The system manages:

- ✅ Student registration  
- ✅ Meal booking and cancellation  
- ✅ Menu display  
- ✅ Monthly bill generation  
- ✅ Data persistence (student records & meal logs)

This project also demonstrates **Modular Programming** and **Separate Compilation** in C by dividing the system into well-defined components.

---

<h2 style="color:#8E24AA; font-size: 28px;">🧱 Key Features</h2>

<h3 style="color:#039BE5; font-size: 24px;">👤 Student Features</h3>

- 📝 Register as a new student  
- 👁️ View and update profile  
- 🍽️ Book meals (Breakfast/Lunch/Dinner)  
- ❌ Cancel meals (with business rules)  
- 📅 Check daily meal status  
- 💳 View monthly bill + auto deduction from balance  

<h3 style="color:#FB8C00; font-size: 24px;">🛠️ Admin Features</h3>

- ➕ Register new students  
- 📂 View all student records  
- 📜 Display mess menu  

---

<h2 style="color:#3949AB; font-size: 28px;">🗂️ Modular Architecture</h2>

The project strictly follows the modular programming structure in C.

```text
src/
├── main.c            // Driver program
├── auth.c/.h         // Admin & Student login
├── student.c/.h      // Student profile management
├── meal.c/.h         // Meal booking logic
├── billing.c/.h      // Bill calculation
└── file_handler.c/.h // File I/O (persistence)
```

<h2 style="color:#00897B; font-size: 28px;">⚙️ Compilation Instructions</h2>
This project uses gcc and a simple Makefile.

🏗️ Build the Program:

bash ```make```

▶️ Run the Program: ```./MessSystem```
 
<h2 style="color:#2C4B9B; font-size: 28px;">💾 Data Persistence</h2>
The system stores data in two files:

students.txt – Student details (roll, name, balance)

meal_log.txt – Logs of meal booking/cancellation

ℹ️ For simplicity, meal logs are saved textually; per-day meal arrays can be extended later.

<h2 style="color:#C62828; font-size: 28px;">🧮 Billing Logic</h2>
💰 Meal charges:

Breakfast: 20
Lunch: 35
Dinner: 45

📊 Billing workflow:

System totals all booked meals

Applies a 5% rebate if total meals < 30

Deducts payable amount from student balance

<h2 style="color:#7B1FA2; font-size: 28px;">🧪 Demonstrated Programming Concepts</h2>
✔️ Modular Programming

✔️ Separate Compilation

✔️ Header Guards

✔️ Struct-Based Data Modeling

✔️ File Handling (Text-based Persistence)

✔️ Menu-driven CLI Application

<h2 style="color:#1E88E5; font-size: 28px;">📌 How the System Works</h2>
👨‍🎓 Student Login using roll number

🧑‍💼 Admin Login (username: admin, password: 1234)

Students can:

👤 View Profile

🍽️ Book Meal

🔄 Cancel Meal

👀 Check Meal Status

🧾 Generate Monthly Bill

🏠 Update Room Number

Admin can:

➕ Register Students

🍛 Display Mess Menu

📋 View Student List

<h2 style="color:#F4511E; font-size: 28px;">🚀 Future Enhancements</h2>
🔐 Password-based student login

📆 Persistent storage of meals_consumed[30]

🗓️ Support for multiple months

📂 CSV/Binary storage

🖥️ GUI/Python interface

<h2 style="color:#0097A7; font-size: 28px;">🧑‍🎓 Ideal For</h2>
🎓 University course projects

💻 Modular C programming demonstrations

📚 Learning file I/O and struct design

🧱 Teaching clean architecture

<h2 style="color:#5E35B1; font-size: 28px;">📸 Sample Program Run (Demo Output)</h2>
 
 
```
 +----------------------------------+
|         Start Application        |
+----------------------------------+
                 |
                 v
+----------------------------------+
|             Main Menu            |
+----------------------------------+
        |                     |
        |                     |
        v                     v
+---------------+     +----------------+
|  Admin Login  |     | Student Login  |
+-------+-------+     +--------+-------+
        |                        |
        v                        v
+---------------+     +------------------------------+
| Admin Actions |     |       Student Actions        |
|---------------|     |------------------------------|
| - Register    |     | - View Profile               |
|   Student     |     | - Book Meal                 |
| - Show Menu   |     | - Cancel Meal               |
| - List        |     | - Check Meal Status         |
|   Students    |     | - Generate Monthly Bill     |
+-------+-------+     +---------------+--------------+
        |                            |
        +-------------+   +----------+
                      |   |
                      v   v
                 +----------------+
                 |  Back to Main  |
                 +----------------+
```
<h2 style="color:#2E7D32; font-size: 28px;">📜 License</h2>
This project is free for academic use and may be modified as needed.
Feel free to ⭐ the repo, fork it, and extend the features for your own university or course work!

# Makefile for MessSystem project

CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I.

SRC = main.c auth.c student.c meal.c billing.c file_handler.c
OBJ = $(SRC:.c=.o)
TARGET = MessSystem

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)

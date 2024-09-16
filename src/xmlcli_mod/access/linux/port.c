#include<sys/io.h>
#include<unistd.h>
#include<stdio.h>
#include<stdint.h>
#include<stdlib.h>

uint8_t *read_port(uint16_t port, uint8_t size)
{
    // Get access to all ports on the system
    iopl(3);

    // Allocate our array to hold port reads
    uint8_t *val = malloc(sizeof(uint8_t) * size);

    if (val)
    {
        for(int i = 0; i < size; i++)
        {
            uint8_t byte = inb(port + i);
            val[i] = byte;
        }
    }

    return val;
}

void write_port(uint16_t port, uint8_t size, uint32_t val)
{
    uint8_t byteToWrite;
    // Get access to all ports on the system
    iopl(3);

    for(int i = 0; i < size; i++)
    {
        byteToWrite = ((val >> (8 * i)) & 0xFF);
        outb(byteToWrite, port + i);
    }
}

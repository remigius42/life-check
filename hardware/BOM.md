<!-- spellchecker: ignore perfboard purecrea -->

# Bill of Materials (BOM)

This document lists all components, materials, and tools required to build the
Life Check system.

## Core Components

| Item                                                                  | Quantity | Route | Notes                                             |
| :-------------------------------------------------------------------- | :------- | :---- | :------------------------------------------------ |
| **[DFRobot 5V IR Switch](https://www.dfrobot.com/product-2644.html)** | 1        | Both  | Includes transmitter and receiver.                |
| **Raspberry Pi**                                                      | 1        | Pi    | Any model with GPIO (Pi Zero W / 2W recommended). |
| **MicroSD Card**                                                      | 1        | Pi    | 8GB or larger (Class 10 recommended).             |
| **ESP32 Dev Board**                                                   | 1        | ESP32 | WROOM DevKit v1 or S3 DevKit.                     |
| **Logic Level Shifter**                                               | 1        | Pi    | BSS138-based (e.g., Purecrea 2-channel).          |
| **Resistor 10 kΩ**                                                    | 1        | ESP32 | 1/4W or 1/8W through-hole.                        |
| **Resistor 20 kΩ**                                                    | 1        | ESP32 | 1/4W or 1/8W through-hole.                        |
| **5V USB Power Supply**                                               | 1        | Both  | 5V / 1A minimum.                                  |
| **USB Cable**                                                         | 1        | Both  | Micro-USB or USB-C (depending on board).          |

## Assembly Materials

| Item                     | Quantity | Route | Notes                                               |
| :----------------------- | :------- | :---- | :-------------------------------------------------- |
| **Dupont Jumpers**       | 1 set    | Both  | Mix of M-F and F-F for connecting components.       |
| **Dupont Housings/Pins** | 1 kit    | Both  | For terminating the bare sensor wires.              |
| **Hook-up Wire**         | 1 spool  | Both  | 28 AWG stranded (for extending sensor leads).       |
| **Heat Shrink Tubing**   | 1 kit    | Both  | 2.5mm or 3mm diameter.                              |
| **Perfboard**            | 1 pc     | ESP32 | Small scrap for the resistor divider circuit.       |
| **M3 Screws**            | 4        | Pi    | 10mm length (for level shifter case).               |
| **Mounting Tape**        | 1 roll   | Both  | 3M VHB or similar for mounting sensors to doorways. |

## Tools

- **Soldering Iron** & **Solder** (Lead-free recommended)
- **Wire Strippers** & **Flush Cutters**
- **Dupont Crimping Tool** (Optional but recommended for clean terminations)
- **Heat Gun** or Lighter (for heat shrink)
- **Screwdriver Set** (PH1/PH2 for case screws)
- **Multimeter** (For verifying connections and voltage divider)

## 3D Printed Parts

See [hardware/3d/README.md](./3d/README.md) for links and files.

- **Main Enclosure**: For Pi Zero or ESP32.
- **Level Shifter Case**: (Pi Route only) To house the BSS138 module.
- **Sensor Brackets**: (Optional) If not using mounting tape directly.

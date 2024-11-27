# IMPETUS Data Cleaning Tool

## Description

The **IMPETUS Data Cleaning Tool** is a modular software designed to ensure data preprocessing. Developed as part of the European project **IMPETUS**, the tool addresses challenges related to data quality, transparency, and trustworthiness in the context of regional climate resilience efforts.

This tool enables the detection and correction of common data artifacts, such as blanks, flatlines, and outliers, in time-series datasets. By integrating algorithms and a configuration system, it facilitates data preparation for subsequent analyses while adhering to the **FAIR data principles** (Findable, Accessible, Interoperable, and Reusable).

## Key Features

- **Artifact Detection and Correction**: Identifies and addresses issues such as:
  - **Blanks**: Missing or undefined values.
  - **Flatlines**: Sensor malfunctions causing repetitive identical values.
  - **Outliers**: Anomalous data points deviating from expected patterns.

- **Modular and Configurable**:
  - The tool processes data based on user-defined configurations in a JSON-like format.
  - Supports a sequence of transformations and imputation strategies tailored to the dataset.

## System Architecture

The Data Cleaning Tool integrates with the broader **IMPETUS Resilience Knowledge Boosters (RKB)** ecosystem. It is implemented in Python, leveraging libraries like Pandas and NumPy for data manipulation. The tool communicates with the **Coordination Module** via RESTful APIs to receive data, process it, and return the cleaned output.

## Example Applications

- Cleaning time-series data collected from climate sensors.
- Preparing datasets for statistical modeling and forecasting.
- Enhancing data quality for storage in Open Data Spaces (ODS) within the IMPETUS framework.

## License

This project is licensed under the **Apache License 2.0**. You may use, modify, and distribute this software in accordance with the terms specified in the license. For more information, refer to the `LICENSE` file in this repository or visit the [Apache 2.0 License page](https://www.apache.org/licenses/LICENSE-2.0).


---

### Note

This README provides an overview of the Data Cleaning Tool's purpose and functionality. For additional context about the IMPETUS project and its objectives, visit the [IMPETUS Project Page](https://climate-impetus.eu/).

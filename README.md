# Emission-reducing deployment of shared office networks

This repository contains the code used for implementing the methods described in our paper titled "Emission-reducing deployment of shared office networks". In this work, we present a generic method based on publicly available data to design a master plan for optimizing the number and placement of coworking spaces in a given area. Our goal is to reduce greenhouse gas emissions linked to car commuting by strategically placing coworking spaces and encouraging commuters to switch to more sustainable modes of transport.

## Overview

Our approach involves three main stages:

1. **Data Collection and Preprocessing:** We collect population data from publicly available sources and preprocess them to convert them into an exploitable form. We filter the population to include only individuals eligible for teleworking based on socio-professional categories.

2. **Decision Model Design:** We design a decision model that determines when an individual would choose to work in a shared office and which transport mode they would use. We consider factors such as travel time, mode of transport, and individual preferences.

3. **Optimization:** We perform optimization using a combination of linear solver and heuristic methods. The objective is to maximize the reduction in car travel distance by strategically placing coworking spaces. We consider the coworking spaces as a networked system, optimizing their collective impact on reducing greenhouse gas emissions.

## Data Sources

We use French population census data provided by INSEE, specifically focusing on professional mobility data. This dataset includes information such as residency municipality, workplace municipality, socio-professional category, transport mode, and number of cars owned by households.

## Implementation Details

### Parameters and Decision Model
- **Isochrone:** Maximum travel time for an employee to consider using a coworking space.
- **Minimum Saved Time:** Minimum time saved required for an employee to switch to a coworking space (set to 10 minutes in this implementation).

### Optimization Algorithms
1. **Integer Programming:**
   - Objective: Maximize the total saved travel distance for all active displacement relationships.
   - Constraints:
     - Select a maximum of *n* coworking spaces.
     - Each individual can choose at most one alternative office.
     - Individuals can choose an office only if it is part of the selected sites.

2. **Heuristic Methods:**
   - **Monte-Carlo Algorithm:**
     - Randomly selects *n* distinct municipalities, weighted by their individual performance.
     - Evaluates solutions iteratively and stops after a specified number of unsuccessful iterations.
   - **Parallel Evolutionary Algorithm:**
     - Uses a structured stochastic approach inspired by natural selection mechanisms.
     - Emulates Darwinian evolution: fittest individuals are allowed to reproduce and form the next generation.
     - Uses parallel implementation with multiple threads for efficient exploration of solutions.

## How to Use

Follow these steps to utilize the code and replicate our research:

1. **Get the Data:**
   - Download French administrative boundaries from [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/decoupage-administratif-communal-francais-issu-d-openstreetmap/). Unzip the file in `data/iris`.
   - Obtain the professional mobility file from [INSEE](https://www.insee.fr/fr/statistiques/fichier/5395749/RP2018_mobpro_csv.zip) and unzip it in `data`.

2. **Clone the Repository:**
   ```
   git clone git@github.com:odyssee-co/tiers-lieux.git
   cd tiers-lieux
   ```

3. **Install Dependencies:**
   ```
   pip install -r requirements.txt
   ```
   Install Equasim Router:
   ```
   cd equasim-java
   mvn clean package -Pstandalone -DskipTests
   ```

4. **Run the Optimization:**
   - Modify parameters and settings in the configuration files (examples provided in `code/conf`).
   - Run the main optimization script.
   ```
   mkdir data/processed
   cd code
   python run.py --conf conf_file.yml
   ```

## Citation

If you find our work useful, kindly consider citing our paper:

*M. Mastio, S. Hörl, M. Balac, V. Loubière. "Emission-reducing deployment of shared office networks." 14th International Conference on Ambient Systems, Networks and Technologies (ANT 2023), Mar 2023, Leuven, Belgium. pp. 315-322, DOI: 10.1016/j.procs.2023.03.041.*

## License

This project is licensed under the GNU GPL License - see the [LICENSE](LICENSE) file for details.

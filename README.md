
# Delivery Routing

Optimised routing using OpenStreetMap for effective delivery system by genetic algorithm in Python.

![App Screenshot](/screenshots/delivery_routing.jpg)

## Installation

Install the following libraries;

folium, pandas, geopandas, matplotlib, networkx, numpy, osmnx, rasterio, scipy, shapely.

```bash
  conda install -c conda-forge folium
  conda install -c anaconda pandas
  conda install -c conda-forge geopandas
  conda install -c conda-forge matplotlib
  conda install -c anaconda networkx
  conda install -c anaconda numpy
  conda install -c conda-forge osmnx
  conda install -c conda-forge rasterio
  conda install -c anaconda scipy
  conda install -c conda-forge shapely
```

for entire package list refer Requirements.txt

Created and Tested in Anaconda Python 3.8

## Usage

Feed the input data on to the respective csv files in the data directory.

- uno - unique identifier,
- lat - latitude,
- lon - longitude.

The program takes only one origin location.

```bash
cd delivery_routing
jupyter notebook delivery_routing.ipynb
```

Additional informations are provided in the notebook.

Run the cells and enjoy the shortest route.

## License

[MIT](https://choosealicense.com/licenses/mit/)

  
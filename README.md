# Belo Horizonte analysis

This repository contains notebooks and data to generate indicators for the city of Belo Horizonte, Minas Gerais, Brazil. The two indicators are:

1. **Heat islands:** Using a statistical matching methodology to evaluate the impact of greening efforts on vacant lots.
2. **Carbon capture:** Evaluating the long-term carbon capture potential of planting over 20,000 trees.

## Usage
Install all necessary packages with `uv`:

```
uv sync
```

Copy the `.env.example` file:

```
cp .env.example .env
```

Fill in the missing variables:

* `PROJECT_NAME`: Name of a valid EarthEngine project
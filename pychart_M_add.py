name: Python package

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]
  schedule:
    - cron: "0 2 * * *"

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 lxml pandas selenium webdriver_manager

      - name: Run Python script
        run: |
          python pychart_M_add.py

      - name: Check git status
        run: |
          git status

      - name: Commit files
        run: |
          git config --global user.email "hyeji1364@gmail.com"
          git config --global user.name "Hyeji1364"
          git add Melonadd/pychart_M_add*.json
          git commit -m "차트 수집 완료" || echo "No changes to commit"

      - name: Push changes
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git push origin main

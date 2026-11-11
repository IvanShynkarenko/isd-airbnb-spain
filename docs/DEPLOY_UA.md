# Розгортання в Databricks Free Edition: покрокова інструкція

Інструкція для команди ISD: від порожнього воркспейсу до робочого пайплайну, дашборду і Genie.
Потрібно близько 40–60 хвилин, з них 15–25 хвилин іде на сам прогін Job.

> **Барселону не завантажуйте і не запускайте**, поки не поставлено тег `week1-final`. Так вимагає умова завдання.

---

## Крок 0. Що вже має бути зроблено

- [ ] Схема і Volume створені (SQL Editor):
  ```sql
  CREATE SCHEMA IF NOT EXISTS workspace.airbnb;
  CREATE VOLUME IF NOT EXISTS workspace.airbnb.raw;
  ```
- [ ] Файли лежать у Volume:
  - `/Volumes/workspace/airbnb/raw/madrid/2026-09-17/listings.csv.gz`
  - `/Volumes/workspace/airbnb/raw/sevilla/2026-09-25/listings.csv.gz`
- [ ] GitHub підключено: аватар → **Settings** → **Linked accounts** → GitHub.
- [ ] Git folder створено: **Workspace** → **Home** → **Create** → **Git folder** → `https://github.com/IvanShynkarenko/isd-airbnb-spain`.

**Як перевірити файли.** **Catalog** → `workspace` → `airbnb` → **Volumes** → `raw`. Відкрийте папки міст: у кожній має бути `listings.csv.gz` розміром близько 12 МБ (Madrid) і 4.6 МБ (Sevilla).

Якщо файлів немає, пайплайн спробує завантажити їх сам. Якщо Databricks не пустить в інтернет, Job впаде з повідомленням, де точно вказані посилання і шлях, куди покласти файл.

---

## Крок 1. Отримати свіжий код

1. **Workspace** → **Home** → папка `isd-airbnb-spain`.
2. Угорі натисніть назву гілки (наприклад `main`) → відкриється вікно Git.
3. Натисніть **Pull**. Гілка має бути `main`.
4. У папці мають з'явитися `notebooks/`, `src/`, `config/`, `jobs/`, `dashboards/`, `genie/`, `docs/`.

---

## Крок 2. Створити Job

1. Відкрийте `notebooks/00_setup_job`.
2. Угорі праворуч у полі compute виберіть **Serverless** (зазвичай він уже вибраний).
3. Натисніть **Run all**.
4. Внизу з'явиться рядок `Job created: https://.../jobs/123456...`. Натисніть на посилання.

> Повторний запуск `00_setup_job` **оновлює** той самий Job, а не створює копію. Його треба перезапускати після кожного `Pull`, якщо змінився `jobs/airbnb_pipeline.json`.

---

## Крок 3. Запустити пайплайн для Мадрида і Севільї

1. **Jobs & Pipelines** → `airbnb_pipeline`.
2. Натисніть **Run now**. Параметри за замовчуванням правильні:
   - `cities` = `["madrid","sevilla"]`
   - `train` = `true`
   - `train_cities` = `["madrid","sevilla"]`
3. Відкрийте запуск (вкладка **Runs** → верхній рядок). Задачі мають іти так:

   ```
   etl_per_city (2 ітерації) → should_train (true) → train → score_per_city (2 ітерації)
   ```

4. Зачекайте, поки всі задачі стануть зеленими. Перша задача кожного ноутбука ставить бібліотеки, на це йде 1–2 хвилини.

**Якщо якась задача червона:** натисніть на неї → **Output** → скопіюйте **весь текст помилки** і надішліть мені.

---

## Крок 4. Перевірити результат

**SQL Editor** → виконайте:

```sql
SELECT city, COUNT(*) AS listings, COUNT(id) AS with_id,
       ROUND(AVG(CASE WHEN split = 'test' THEN 1 ELSE 0 END), 3) AS test_share
FROM workspace.airbnb_gold.features GROUP BY city ORDER BY city;
```
Очікується: `madrid 23109 23109 ≈0.20`, `sevilla 8375 8375 ≈0.20`. Тобто `listings` = `with_id`, а `test_share` між 0.18 і 0.22.

```sql
SELECT city, population, n, ROUND(mae_model, 2) AS mae_model, ROUND(mae_baseline, 2) AS mae_baseline, model_version
FROM workspace.airbnb_gold.model_metrics ORDER BY population DESC, city;
```
Очікується приблизно (може трохи відрізнятися через версію scikit-learn):

| city | population | mae_model | mae_baseline |
|---|---|---|---|
| all | ok | ≈ 49.7 | ≈ 66.0 |
| madrid | ok | ≈ 49.9 | ≈ 67.1 |
| sevilla | ok | ≈ 49.1 | ≈ 63.4 |

Головне — щоб `mae_model` була помітно меншою за `mae_baseline` у кожному рядку.

**Надішліть мені скриншот цієї таблиці.** Я оновлю `reports/week1_metrics.md` цифрами з Databricks.

---

## Крок 5. Коментарі до таблиць (для Genie)

1. Відкрийте файл `genie/table_comments.sql` у Git folder і скопіюйте весь текст.
2. **SQL Editor** → нова вкладка → вставте → **Run all**.

---

## Крок 6. Імпортувати дашборд

1. Завантажте файл на комп'ютер: на GitHub відкрийте `dashboards/airbnb_spain.lvdash.json` → кнопка **Download raw file** (стрілка вниз праворуч над кодом).
2. У Databricks: **Dashboards** → біля синьої кнопки **Create dashboard** натисніть стрілку ▾ → **Import dashboard from file** → виберіть файл → **Import dashboard**.
3. Якщо дашборд просить warehouse, виберіть **Serverless Starter Warehouse**.
4. Перегляньте три сторінки: **City overview**, **Madrid vs Sevilla**, **Model**. Якщо все гаразд, натисніть **Publish** угорі праворуч.

**Якщо імпорт не пройшов** або якийсь графік показує помилку, зробіть скриншот і надішліть мені. Запасний шлях: створити дашборд вручну, взявши запити з `dashboards/datasets.sql` (кожен блок `-- name:` — окремий dataset).

---

## Крок 7. Створити Genie Agent

1. **Create** (або **New**) → **Genie Agent**.
2. **Data** → **Add** → додайте 5 таблиць у такому порядку:
   1. `workspace.airbnb_gold.city_metrics`
   2. `workspace.airbnb_gold.neighbourhood_metrics`
   3. `workspace.airbnb_gold.predictions`
   4. `workspace.airbnb_gold.model_metrics`
   5. `workspace.airbnb_silver.listings`
3. Назва: `Airbnb Spain (Team ISD)`.
4. **Instructions** → **General instructions**: вставте блок з `genie/instructions.md` (від ```` ``` ```` до ```` ``` ````).
5. **Instructions** → **SQL queries** → **Add**. Додайте 3 запити з `genie/example_questions.sql`: назва — це текст після `-- question:`, тіло — сам SQL.
6. Поставте три запитання з умови і порівняйте з очікуваними відповідями:

| запитання | очікувана відповідь |
|---|---|
| What is the median price of entire homes in City A? | Madrid ≈ 174 EUR |
| Which neighbourhoods in City B have the most listings? | Alfalfa (938), Santa Cruz (688), Arenal (656)… |
| Where does the model under-price listings the most? | El Viso (−105), Castellana (−102), Jerónimos (−94) у Madrid; Triana Oeste (−55) у Sevilla |

Якщо відповідь інша, натисніть **Show code** під відповіддю, скопіюйте SQL і надішліть мені.

---

## Крок 8 (необов'язково). Прогнати EDA в Databricks

`notebooks/eda_madrid_sevilla.ipynb` → **Run all**. Він читає ті самі таблиці, тому працює лише після кроку 3.

---

## Типові помилки

| що бачите | причина | що зробити |
|---|---|---|
| `RawFileMissing: Raw file for 'madrid' is not in the Volume and the download failed` | Free Edition не пускає в інтернет, а файлу немає у Volume | Завантажте файл за посиланням з повідомлення і покладіть точно за вказаним шляхом. Або натисніть **Verify identity** угорі воркспейсу, щоб відкрити інтернет |
| `ModuleNotFoundError: No module named 'airbnb'` | ноутбук запущено не з Git folder (наприклад, скопійований окремо) | Запускайте ноутбуки з папки `isd-airbnb-spain/notebooks/` |
| `ModuleNotFoundError: No module named 'yaml'` або `'sklearn'` в EDA | EDA-ноутбук не ставить бібліотеки сам | Додайте першою клітинкою `%pip install -q -r ../requirements-databricks.txt` і запустіть ще раз |
| помилка в `00_setup_job` про `for_each_task` або `condition_task` | API Job змінився | Надішліть мені текст. Тимчасово: **Jobs & Pipelines** → **Create** → **Job** → ⋮ → **Edit as JSON**/**Switch to code**, вставте `jobs/airbnb_pipeline.json`, замінивши `{REPO}` на шлях до папки (напр. `/Users/you@mail/isd-airbnb-spain`) |
| `train` падає з помилкою MLflow / `PERMISSION_DENIED` на моделі | немає прав на реєстрацію моделі в Unity Catalog | Надішліть текст помилки; можливий обхід — зберігати модель лише в MLflow run |
| `score_per_city` пропущено (сірий) | `train` не відпрацював | Подивіться помилку в `train` |
| Job стоїть у черзі | на Free Edition обмежена кількість одночасних запусків | Зачекайте або зупиніть інші запуски |

---

## Що далі

Коли кроки 3–7 пройдуть успішно, напишіть мені. Я поставлю тег `week1-final`, і перший тиждень буде заморожено.
Барселону запускаємо лише після цього.

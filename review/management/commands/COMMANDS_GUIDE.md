# Management Commands Documentation

This directory contains Django management commands for populating the database with test data.

## Commands

### 1. `populate_campuses`
Creates 4 random cities as campuses.

```bash
python manage.py populate_campuses
```

**Output:**
- 4 random campuses selected from a list of Thai cities
- Clears existing campuses first

---

### 2. `populate_courses`
Creates 10 courses with random codes, descriptions, and credits (1-3).

```bash
python manage.py populate_courses
```

**Features:**
- Random course codes (e.g., CS302, MATH250)
- Generated descriptions using Faker
- Credit hours: randomly 1, 2, or 3
- Clears existing courses first

---

### 3. `populate_professors`
Creates 15 professors with random emails, image URLs, and education descriptions.

```bash
python manage.py populate_professors
```

**Features:**
- Random unique emails (firstname.lastname@university.edu)
- Default image URL from Freepik
- Random education/background descriptions
- Clears existing professors first

---

### 4. `populate_sections`
Creates sections for each course (1-5 sections per course) with teaching assignments.

```bash
python manage.py populate_sections
```

**Features:**
- 1-5 sections randomly assigned per course
- Creates TimeSlots (Mon-Fri, 8am-5pm)
- Assigns exactly 1 professor per section
- Links sections with schedule times
- Clears existing sections first

---

### 5. `populate_users`
Creates 50 random users with disabled passwords.

```bash
python manage.py populate_users
```

**Features:**
- Username format: "FirstName LastName"
- Email format: "firstnamelastname@example.mail"
- Passwords are disabled (unusable)
- is_active=True, is_staff=False
- Clears existing non-superuser accounts first

---

### 6. `populate_tags`
Creates 5 review tags.

```bash
python manage.py populate_tags
```

**Tags created:**
- Exam
- Homework
- Attendance
- Teaching Quality
- Course Content

---

### 7. `populate_reviews`
Creates ~100 reviews with tags, ratings, and various associations.

```bash
python manage.py populate_reviews
```

**Features:**
- ~100 reviews with random content
- Rating: 1-5 stars
- Tags: 1-3 random tags per review
- Associations:
  - 60% have a section (implies course)
  - 40% have a professor (with course)
- Random creation dates within the last year
- Incognito flag: randomly True or False
- Clears existing reviews first

---

### 8. `populate_votes_and_bookmarks`
Creates user votes, reports, and bookmarks for reviews.

```bash
python manage.py populate_votes_and_bookmarks
```

**Features:**
- **Votes:** ~30% chance each user votes on each review
  - Vote type: upvote (1) or downvote (-1)
  - ~1,500+ votes created
- **Reports:** ~5% of reviews get reported
  - 1-3 users per review
  - Random report reasons (spam, misinformation, etc.)
  - ~7 reports typically created
- **Bookmarks:** Each user has 5-15 bookmarks
  - 70% bookmark reviews
  - 30% bookmark courses only
  - ~73 bookmarks typically created

---

## Recommended Execution Order

For a fresh database setup, run commands in this order:

```bash
python manage.py populate_campuses
python manage.py populate_courses
python manage.py populate_professors
python manage.py populate_sections
python manage.py populate_users
python manage.py populate_tags
python manage.py populate_reviews
python manage.py populate_votes_and_bookmarks
```

---

## Data Summary

After running all commands, you'll have:
- **Campuses:** 4 random cities
- **Courses:** 10 courses
- **Professors:** 15 professors
- **Sections:** ~30 sections (1-5 per course)
- **Users:** 50 regular users + superusers
- **Tags:** 5 tags
- **Reviews:** ~100 reviews
- **Votes:** ~1,500+ upvotes/downvotes
- **Reports:** ~7 reports
- **Bookmarks:** ~73 bookmarks

---

## Notes

- Each command automatically clears existing data before creation
- All commands use randomization for realistic test data
- Unique constraints (emails, usernames) are respected
- Commands use bulk_create for efficiency
- Faker library is used for generating realistic content

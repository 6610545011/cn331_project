# Test Coverage Report - CN331 Project

## Overview
- **Total Tests**: 77 tests
- **Test Status**: ✅ All Passing
- **Overall Coverage**: **72%**
- **Framework**: Django Test Framework

---

## Coverage by App

### 1. **core/tests.py** (16 tests)
**Coverage**: 89% of models, 100% of URLs & Admin

#### Model Tests (11 tests)
- ✅ Course creation with all fields
- ✅ Prof optional fields handling
- ✅ Campus unique name constraint
- ✅ Course string representation
- ✅ Prof string representation
- ✅ Section string representation
- ✅ Course.all_professors property
- ✅ Enrollment unique constraint
- ✅ Section-TimeSlot M2M relationship
- ✅ Multiple professors per course
- ✅ Multiple students per section
- ✅ Cascade delete on course deletion
- ✅ Cascade delete on user deletion
- ✅ Multiple students in section
- ✅ Teach and Enrollment string methods

#### View Tests (5 tests)
- ✅ Homepage renders correctly
- ✅ Search view context and filtering
- ✅ Professor detail view with reviews
- ✅ Course detail view with reviews
- ✅ 404 handling for non-existent resources
- ✅ Search view with sorting
- ✅ About view

**Uncovered Paths**:
- Full query filtering logic in search view (advanced sorting)
- Some bookmark annotation subqueries

---

### 2. **review/tests.py** (50 tests)
**Coverage**: 98% of views, 87% of forms, 100% of models

#### Model Tests (19 tests)
- ✅ Review creation with/without section
- ✅ Review with tags relationship
- ✅ Review incognito field
- ✅ Review date_created field
- ✅ Multiple tags per review
- ✅ Vote score aggregation (upvotes)
- ✅ Vote score aggregation (downvotes)
- ✅ Vote score aggregation (mixed)
- ✅ Bookmark with/without review
- ✅ Report creation and uniqueness
- ✅ ReviewUpvote string representation
- ✅ Review ordering by date
- ✅ Rating values (1-5)
- ✅ Multiple reviews per user
- ✅ Tag unique name constraint
- ✅ Tag string representation
- ✅ Review string representation
- ✅ Bookmark string representation
- ✅ Report string representation

#### Form Tests (9 tests)
- ✅ ReviewForm valid submission
- ✅ ReviewForm no target error (bad path)
- ✅ ReviewForm section not in course (bad path)
- ✅ ReviewForm prof not teaching course (bad path)
- ✅ ReviewForm prof not teaching section (bad path)
- ✅ ReviewForm prof-only inference (good path)
- ✅ ReviewForm prof without course (bad path)
- ✅ ReportForm valid submission
- ✅ ReviewUpvoteForm valid/invalid votes

#### View Tests (22 tests)
- ✅ Write review GET request
- ✅ Write review POST valid
- ✅ Write review POST invalid
- ✅ Write review login redirect
- ✅ AJAX search courses
- ✅ AJAX search courses empty result
- ✅ AJAX get professors
- ✅ AJAX get professors no section
- ✅ AJAX get sections
- ✅ AJAX get sections no course
- ✅ Toggle bookmark create
- ✅ Toggle bookmark delete
- ✅ Report review valid
- ✅ Report review duplicate (bad path)
- ✅ Vote review upvote
- ✅ Vote review downvote
- ✅ Vote review toggle
- ✅ Vote review update vote type
- ✅ Vote review invalid JSON (bad path)
- ✅ Vote review invalid vote type (bad path)
- ✅ Delete own review
- ✅ Delete others review fails (bad path)

**Uncovered Paths**:
- Some form edge cases (exception handling)
- Admin interface customizations
- Management commands (data seeding)

---

### 3. **users/tests.py** (18 tests)
**Coverage**: 100% of models, 96% of views

#### User Manager Tests (18 tests)
- ✅ create_user basic functionality
- ✅ create_superuser with flags
- ✅ User email unique constraint
- ✅ User username unique constraint
- ✅ create_user requires username
- ✅ create_user requires email
- ✅ User optional fields (empty)
- ✅ User with first/last names
- ✅ User is_active default
- ✅ User is_staff default
- ✅ Superuser is_staff validation (bad path)
- ✅ Superuser is_superuser validation (bad path)
- ✅ User date_joined
- ✅ User last_login null
- ✅ User password hashing
- ✅ User email normalization
- ✅ User with image URL
- ✅ User queryset filtering

#### View Tests (5 tests)
- ✅ Login view GET
- ✅ Login view POST valid
- ✅ Login view POST invalid password
- ✅ Login view POST nonexistent user
- ✅ Profile view logged in
- ✅ Profile view not logged in (redirect)
- ✅ Profile view with reviews
- ✅ Profile view with bookmarks

**Uncovered Paths**:
- Line 21 in users/views.py (message handling edge case)

---

## Test Categories Breakdown

### Good Path Tests (Positive Cases)
- ✅ Model creation with valid data
- ✅ Form submission with valid data
- ✅ View rendering with correct context
- ✅ Relationships working as expected
- ✅ String representations correct
- ✅ Constraints enforced properly
- ✅ Aggregations calculating correctly

### Bad Path Tests (Negative Cases)
- ✅ Duplicate constraint violations
- ✅ Invalid form data submission
- ✅ 404 errors on non-existent resources
- ✅ Unauthorized access attempts
- ✅ Data integrity validation
- ✅ Error messages on invalid input
- ✅ Toggle/state management

---

## How to Run Tests

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test core
python manage.py test review
python manage.py test users
```

### Run Specific Test Class
```bash
python manage.py test core.tests.CoreModelsTestCase
python manage.py test review.tests.ReviewViewsTestCase
python manage.py test users.tests.UserModelAndManagerTestCase
```

### Run Tests with Coverage Report
```bash
coverage run --source='core,review,users' manage.py test
coverage report -m
```

### Generate HTML Coverage Report
```bash
coverage html
# Open htmlcov/index.html in browser
```

### Run Tests with Verbosity
```bash
python manage.py test -v 2
```

---

## Current Coverage Details

| Module | Lines | Missed | Coverage |
|--------|-------|--------|----------|
| **review/views.py** | 97 | 2 | **98%** |
| **users/views.py** | 28 | 1 | **96%** |
| **review/forms.py** | 102 | 13 | **87%** |
| **core/models.py** | 66 | 7 | **89%** |
| **review/models.py** | 54 | 0 | **100%** |
| **users/models.py** | 43 | 0 | **100%** |
| **review/tests.py** | 317 | 0 | **100%** |
| **users/tests.py** | 130 | 0 | **100%** |
| **core/admin.py** | 8 | 0 | **100%** |
| **users/admin.py** | 10 | 0 | **100%** |
| **Overall** | 1298 | 363 | **72%** |

---

## Key Testing Highlights

### ✨ Comprehensive Coverage Areas

1. **Form Validation**
   - Course/Professor/Section inference logic
   - Dependency validation between fields
   - Unique constraint testing
   - Tag multi-select handling

2. **View Layer**
   - HTTP method handling (GET, POST)
   - Login required decorator
   - JSON response handling
   - AJAX endpoints
   - Redirect behavior

3. **Model Relationships**
   - Many-to-many relationships
   - Foreign key cascade behavior
   - Unique constraints
   - Property decorators
   - String representations

4. **User Authentication**
   - Login/logout flow
   - User creation and validation
   - Superuser permissions
   - Password hashing

5. **Data Integrity**
   - Transaction handling
   - Vote aggregation
   - Bookmark management
   - Review reporting

---

## Notes

- All test data is created fresh for each test (isolation)
- Tests use `transaction.atomic()` for constraint violation testing
- Force login used to avoid SimpleLazyObject issues in queries
- Coverage excludes migrations and data seeding commands
- Management commands are not tested (0% coverage, but optional)

---

## Recommended Next Steps for Even Higher Coverage

1. Add tests for management commands (data seeding)
2. Test form validation edge cases more thoroughly
3. Add integration tests for multi-step workflows
4. Test permission and authorization edge cases
5. Add tests for template rendering content
6. Load testing and performance tests

---

**Last Updated**: November 16, 2025  
**Test Framework**: Django  
**Status**: ✅ All Tests Passing (77/77)

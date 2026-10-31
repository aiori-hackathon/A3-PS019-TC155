# Privexis synthetic demo datasets

These fixtures are generated synthetic data. Each CSV contains 20 rows and 11 columns. The matching SQLite file contains the same fixture in a table named `demo_records`.

Every fixture has eight class-specific candidate fields and three look-alike negative fields: `order_id`, `product_name`, and `event_count`.

| Class | Files | Columns |
| --- | --- | --- |
| C1 Personal identity | `personal_identity.csv`, `personal_identity.sqlite3` | `birthdate`, `family_name`, `person_age`, `child_name`, `individual_name`, `dependent_name`, `dob`, `given_name`, `order_id`, `product_name`, `event_count` |
| C2 Contact information | `contact_information.csv`, `contact_information.sqlite3` | `contact_number`, `customer_email`, `primary_phone`, `emergency_phone`, `e_mail_address`, `secondary_email`, `email`, `telephone`, `order_id`, `product_name`, `event_count` |
| C3 Government identifiers | `government_identifiers.csv`, `government_identifiers.sqlite3` | `voter_card_number`, `driving_license_number`, `license_number`, `voter_id`, `electoral_id`, `driver_license_number`, `voter_card_id`, `pan_number`, `order_id`, `product_name`, `event_count` |
| C4 Financial information | `financial_information.csv`, `financial_information.sqlite3` | `payment_card_number`, `bank_acc_no`, `upi_address`, `card_number`, `beneficiary_account_number`, `ifsc_code`, `current_account_number`, `routing_ifsc`, `order_id`, `product_name`, `event_count` |
| C5 Location / address | `location_address.csv`, `location_address.sqlite3` | `location_coordinates`, `postal_address`, `mailing_address`, `home_address`, `street_address`, `gps_coordinates`, `latitude`, `geo_longitude`, `order_id`, `product_name`, `event_count` |

Example synthetic rows include `Synthetic Person 001`, `person001@example.invalid`, `TESTVOTER0001`, `synthetic001@upi.invalid`, and `1 Synthetic Lane`. These are fabricated test values, not real identifiers or people.

Upload an individual CSV or SQLite file in Privexis. ZIP archives are for downloading and unpacking; the upload screen accepts CSV and SQLite files directly.

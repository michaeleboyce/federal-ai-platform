# FedRAMP Marketplace Data Browser

A comprehensive web application for browsing and managing FedRAMP (Federal Risk and Authorization Management Program) marketplace data.

## 📋 Overview

This project provides:
- **Backend**: Python scripts to fetch and manage FedRAMP product data
- **Database**: SQLite database with all 615 FedRAMP products
- **Frontend**: Next.js web application for browsing, searching, and filtering products
- **Data Source**: Official JSON API from GSA's FedRAMP marketplace

## 🏗️ Project Structure

```
fedramp/
├── backend/              # Python data fetching & database management
│   ├── db.py            # SQLite database schema and operations
│   ├── load_csv.py      # Load data from CSV (legacy)
│   ├── fetch_json.py    # Fetch data from official JSON API ⭐
│   ├── scraper.py       # HTML scraper (not needed - use JSON instead)
│   └── requirements.txt # Python dependencies
├── data/                 # Data storage
│   ├── fedramp.db       # SQLite database
│   ├── fedramp_products.json # Latest JSON data from API
│   └── html/            # (Optional) HTML files if manually collected
├── frontend/             # Next.js web application
│   ├── app/             # Next.js app directory
│   ├── lib/             # Database utilities
│   └── package.json     # Node dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+ and pnpm
- Git

### 1. Fetch Latest Data

```bash
cd backend
pip3 install -r requirements.txt
python3 fetch_json.py
```

This fetches the latest data from the official FedRAMP JSON API:
`https://raw.githubusercontent.com/GSA/marketplace-fedramp-gov-data/refs/heads/main/data.json`

### 2. Load Data into Database

```bash
python3 load_csv.py  # If you have a CSV file
# OR use the JSON data directly in the frontend
```

### 3. Start the Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📊 Data Source

### Official JSON API ⭐ **RECOMMENDED**

The best way to get FedRAMP data is from the official JSON API maintained by GSA:

- **URL**: `https://raw.githubusercontent.com/GSA/marketplace-fedramp-gov-data/refs/heads/main/data.json`
- **GitHub**: https://github.com/GSA/marketplace-fedramp-gov-data
- **Updates**: Regularly updated by GSA
- **Data**: 615 products with 40+ fields per product

#### Available Fields:
- Basic Info: `id`, `name`, `csp` (provider), `cso` (offering)
- Status: `status`, `authorization`, `reuse`
- Dates: `ready_date`, `auth_date`, `annual_assessment`
- Technical: `service_model`, `deployment_model`, `impact_level`
- Business: `uei`, `small_business`, `business_function`
- Contact: `sales_email`, `security_email`, `website`
- Description: `service_desc`, `fedramp_msg`
- And many more...

### Alternative: CSV Export

You can also download a CSV from the FedRAMP marketplace website, though it has fewer fields than the JSON API.

### HTML Scraping (Not Recommended)

The marketplace website has protection against automated scraping. See `backend/SCRAPING_NOTES.md` for details and alternatives.

## 🔍 Features

### Current Implementation
- ✅ Fetch data from official JSON API
- ✅ SQLite database with full schema
- ✅ CSV import functionality
- ✅ Next.js frontend setup
- ✅ Database query utilities

### Planned Features
- 🔄 Product listing with search and filters
- 🔄 Product detail pages
- 🔄 Export functionality
- 🔄 Custom column management
- 🔄 Data refresh automation

## 🛠️ Development

### Backend Scripts

**Fetch Latest JSON Data** (Recommended):
```bash
python3 backend/fetch_json.py
```

**Load CSV to Database**:
```bash
python3 backend/load_csv.py
```

**Check Scraper Stats**:
```bash
python3 backend/scraper.py --stats
```

### Database

The SQLite database (`data/fedramp.db`) contains:
- All product information from CSV/JSON
- Tracking for HTML scraping status
- Timestamps for data updates

**Schema**:
- `fedramp_id`: Unique product ID
- `cloud_service_provider`: Provider name
- `cloud_service_offering`: Product name
- `service_description`: Detailed description
- `status`: Authorization status
- `service_model`: SaaS/PaaS/IaaS
- Many more fields...

### Frontend

Built with:
- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **better-sqlite3** for database access

## 📝 Notes

### Why Not Scrape HTML?

The FedRAMP marketplace website has protection against automated scraping. When attempting to access pages programmatically, they return empty HTML.

**Solution**: Use the official JSON API instead! It's:
- ✅ More reliable
- ✅ More complete data
- ✅ Officially supported
- ✅ Regularly updated
- ✅ No rate limiting issues

See `backend/SCRAPING_NOTES.md` for technical details.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is for personal/educational use. FedRAMP data is public domain as a US government resource.

## 🔗 Resources

- [FedRAMP Official Site](https://www.fedramp.gov/)
- [FedRAMP Marketplace](https://marketplace.fedramp.gov/)
- [Official JSON Data (GitHub)](https://github.com/GSA/marketplace-fedramp-gov-data)
- [FedRAMP API Example](https://github.com/Rene2mt/marketplace-fedramp-api)

## 📧 Questions?

For questions about FedRAMP data or the marketplace, contact: info@FedRAMP.gov

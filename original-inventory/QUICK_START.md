# FedRAMP Marketplace Browser - Quick Start Guide

## 🚀 Start the Application

The development server is already running at:
**http://localhost:3000**

If you need to restart it:
```bash
cd /Users/michaelboyce/Documents/Programming/ifp/fedramp/frontend
pnpm dev
```

## 🔍 How to Use Search

### Search Box
Located at the top of the main page. Search across:
- Provider names
- Product offerings
- Service names (searches inside the service lists!)
- Descriptions
- FedRAMP IDs

### Example Searches

#### Find AWS Products with Amazon Bedrock
```
Type: Bedrock
Result: 2 products (AWS US East/West, AWS GovCloud)
```

#### Find All Amazon Products
```
Type: Amazon
Result: All AWS products
```

#### Find Products with Lambda
```
Type: Lambda
Result: All products that include AWS Lambda service
```

#### Find Microsoft Products
```
Type: Microsoft
Result: All Microsoft Azure and related products
```

#### Find Specific Product by ID
```
Type: F1603047866
Result: AWS GovCloud
```

## ↕️ How to Use Sorting

### Sortable Columns
Click any of these column headers to sort:

1. **Provider** - Sort alphabetically by company name
2. **Offering** - Sort alphabetically by product name
3. **Services** - Sort by number of services (find products with most/least services)
4. **Auth Date** - Sort by authorization date (find newest/oldest)

### Sorting Indicators
- First click: Ascending order (↑)
- Second click: Descending order (↓)
- Blue arrow shows which column is currently sorted

## 📄 Pagination

### Items Per Page
Choose how many products to show:
- 25 per page (default)
- 50 per page
- 100 per page
- All (show all results)

### Navigation
- Use "Previous" and "Next" buttons
- Page counter shows current page
- Automatically resets to page 1 when searching

## 📊 Common Tasks

### Task 1: Find All Products with a Specific Service
**Example: Which products include Amazon Bedrock?**
1. Open http://localhost:3000
2. Type "Bedrock" in search box
3. See 2 products listed
4. Click "View Details" on either one
5. Scroll to "Authorized Services" section
6. See "Amazon Bedrock" in the list

### Task 2: Find Products with Most Services
**Example: Which cloud provider offers the most services?**
1. Open http://localhost:3000
2. Click "Services" column header twice (descending)
3. See AWS US East/West at top with 154 services
4. See AWS GovCloud second with 136 services

### Task 3: Find Recently Authorized Products
**Example: What's newly authorized?**
1. Open http://localhost:3000
2. Click "Auth Date" column header twice (descending)
3. See most recent authorizations at top

### Task 4: Explore a Specific Product
**Example: See all services in AWS GovCloud**
1. Open http://localhost:3000
2. Search "GovCloud" or scroll to find it
3. Click "View Details"
4. Scroll to "Authorized Services (136)" section
5. See complete list including:
   - Amazon Bedrock
   - Amazon SageMaker AI
   - AWS Lambda
   - Amazon S3
   - And 132 more!

### Task 5: Find Products by Provider
**Example: See all Microsoft products**
1. Open http://localhost:3000
2. Type "Microsoft" in search box
3. See all Microsoft products
4. Click "Provider" column to sort alphabetically

## 💡 Pro Tips

### Combine Search and Sort
1. Search for a term (e.g., "Amazon")
2. Then sort by services to see which Amazon product has most services
3. Or sort by date to see newest Amazon products

### Find Specific Technologies
Search for specific services you need:
- "Bedrock" - AI/ML service
- "Lambda" - Serverless computing
- "S3" - Object storage
- "Kubernetes" - Container orchestration
- "PostgreSQL" - Database

### Check Service Availability
1. Search for a provider (e.g., "AWS")
2. Click into each product
3. Check "Authorized Services" section
4. See exactly which services are included

### Compare Products
1. Search for similar products
2. Open multiple tabs
3. Compare service lists side-by-side
4. Check authorization dates and impact levels

## 📈 Statistics

View the dashboard at the top of the main page:
- **Total Products**: 615
- **Providers**: ~200 unique providers
- **Active Products**: Currently active authorizations
- **Total Services**: 10,000+ services across all products

## 🆘 Troubleshooting

### Search Returns No Results
- Check spelling
- Try shorter search terms
- Try searching provider name instead of service name

### Page Loads Slowly
- If showing "All" items, switch to 50 or 100 per page
- Browser may be slow with 615 items at once

### Want to Refresh Data
```bash
cd /Users/michaelboyce/Documents/Programming/ifp/fedramp/backend
python3 fetch_json.py
```
Then refresh your browser.

## 📚 More Information

- **Full Documentation**: See `README.md`
- **Feature List**: See `FEATURES.md`
- **Project Summary**: See `SUMMARY.md`
- **Data Source**: https://github.com/GSA/marketplace-fedramp-gov-data

## 🎯 Quick Reference

| Action | How To |
|--------|--------|
| **Search** | Type in search box at top |
| **Sort** | Click column header |
| **Change items per page** | Use dropdown next to search |
| **View details** | Click "View Details →" link |
| **See all services** | Open product detail page, scroll to "Authorized Services" |
| **Find Bedrock** | Search "Bedrock", see 2 AWS products |
| **Reset search** | Clear search box or click ✕ |

---

**🎉 You're all set! Visit http://localhost:3000 to start exploring!**

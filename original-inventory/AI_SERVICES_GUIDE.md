# AI Services Analysis - User Guide

## 🎉 Analysis Complete!

All 615 FedRAMP products have been analyzed using **Claude Haiku 4.5** to identify AI, Generative AI, and Large Language Model services.

## 🚀 How to Access

### View AI Services Dashboard
**URL**: http://localhost:3000/ai-services

Or click the **"🤖 AI Services"** button in the header of the main page.

## 🔍 What Was Analyzed

The analysis examined:
- **All 615 FedRAMP products**
- **10,000+ individual services** across all products
- **Service names + product descriptions** for full context
- Using **Claude Haiku 4.5** for intelligent AI detection

## 📊 AI Categories

Services were classified into three categories:

### 1. **AI/ML** (Blue Badge)
- General Artificial Intelligence
- Machine Learning platforms
- AI-powered analytics
- Computer Vision
- Speech Recognition
- Examples: Amazon SageMaker, Azure Machine Learning

### 2. **Generative AI** (Green Badge)
- AI that generates new content
- Text generation
- Image generation
- Code generation
- Examples: Amazon Bedrock, Azure OpenAI

### 3. **LLM** (Orange Badge)
- Large Language Model services
- Natural language processing
- Chatbots and conversational AI
- Text analysis
- Examples: Amazon Bedrock (for Claude, etc.), Azure OpenAI (for GPT-4)

## 📋 Dashboard Features

### Filter by AI Type
- **All**: See all AI-related services
- **AI/ML**: Show only general AI/ML services
- **GenAI**: Show only Generative AI services
- **LLM**: Show only LLM services

### Search
Search across:
- Provider names (e.g., "Amazon", "Microsoft")
- Product names (e.g., "AWS GovCloud")
- Service names (e.g., "Bedrock", "SageMaker")
- Descriptions

### Sort Columns
Click any column header to sort:
- Provider (alphabetically)
- Product (alphabetically)
- Service (alphabetically)
- Status (FedRAMP status)
- Impact (impact level)

### Table Columns

| Column | Description |
|--------|-------------|
| **Provider** | Cloud service provider (AWS, Microsoft, Google, etc.) |
| **Product** | FedRAMP product name |
| **Service** | Specific AI service name |
| **AI Type** | Badges showing AI, GenAI, and/or LLM |
| **Description** | Why this service is AI-related (from Claude's analysis) |
| **Status** | FedRAMP authorization status |
| **Impact** | Impact level (Low/Moderate/High) |
| **Actions** | Link to view full product details |

## 🎯 Example Use Cases

### Find Services with Generative AI
1. Go to http://localhost:3000/ai-services
2. Click the **"GenAI"** filter button
3. See all Generative AI services

### Find AWS AI Services
1. Go to http://localhost:3000/ai-services
2. Type "Amazon" in the search box
3. See all AWS AI services including Bedrock, SageMaker, Comprehend, etc.

### Find LLM Services
1. Go to http://localhost:3000/ai-services
2. Click the **"LLM"** filter button
3. See all Large Language Model services

### Check Which Products Include Amazon Bedrock
1. Go to http://localhost:3000/ai-services
2. Search for "Bedrock"
3. See AWS US East/West and AWS GovCloud

## 📈 Statistics Dashboard

At the top of the AI Services page, you'll see:
- **Total AI Services**: All AI-related services found
- **AI/ML Services**: Count of general AI services
- **Generative AI**: Count of GenAI services
- **LLM Services**: Count of LLM services
- **Products**: Number of products with AI services
- **Providers**: Number of providers offering AI services

## 🔄 Re-running the Analysis

If you want to re-analyze (e.g., after updating the product data):

```bash
cd /Users/michaelboyce/Documents/Programming/ifp
python3 fedramp/backend/analyze_ai_services.py --workers 10
```

This will:
- Clear previous analysis results
- Analyze all 615 products again
- Take about 15-30 minutes
- Cost approximately $5-10 (Claude Haiku is very cheap)

## 💾 Database

Analysis results are stored in:
```
fedramp/data/fedramp.db
```

Table: `ai_service_analysis`

You can query this database directly if needed.

## 🤖 About the Analysis

### Model Used
- **Claude Haiku 4.5** by Anthropic
- Fast, accurate, and cost-effective
- Excellent at understanding technical context

### Analysis Methodology
For each product, Claude analyzed:
1. Product name and description
2. All services listed in that product
3. Technical context about the services
4. Determined if each service relates to AI, GenAI, or LLMs
5. Provided explanation of why it's AI-related

### Quality Assurance
- Context-aware: Analyzed services with their product descriptions
- Conservative: Only flagged clear AI services
- Detailed: Provided explanations for each classification
- Comprehensive: Analyzed all 615 products

## 📝 Example Results

### AWS GovCloud
**AI Services Found:**
- Amazon Bedrock (AI, GenAI, LLM)
- Amazon SageMaker AI (AI)
- Amazon Comprehend (AI)
- Amazon Rekognition (AI - Computer Vision)
- Amazon Lex (AI - Conversational)
- Amazon Polly (AI - Text-to-Speech)
- Amazon Transcribe (AI - Speech-to-Text)
- Amazon Translate (AI - Translation)
- Amazon Kendra (AI - Search)
- And more...

### Azure Government
**AI Services Found:**
- Azure OpenAI Service (AI, GenAI, LLM)
- Azure Cognitive Services (AI)
- Azure Machine Learning (AI)
- And more...

## 🔗 Next Steps

1. **Explore the Dashboard**: http://localhost:3000/ai-services
2. **Filter by Type**: Find specific AI capabilities
3. **Search for Services**: Look for specific technologies
4. **View Product Details**: Click "View Product →" for full info
5. **Compare Options**: Sort and filter to find the best fit

## ⚙️ Technical Details

- **Analysis Job**: `backend/analyze_ai_services.py`
- **Database Functions**: `backend/db.py`
- **Frontend Page**: `frontend/app/ai-services/page.tsx`
- **API Used**: Anthropic Claude Haiku 4.5
- **Parallel Workers**: 10 concurrent API calls
- **Total Time**: ~2-3 minutes for 615 products

## 🎊 Success!

You now have a comprehensive database of FedRAMP-authorized AI services, searchable and filterable through an intuitive web interface!

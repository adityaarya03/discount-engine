#!/bin/bash
# Reset database and seed with new generic design

echo "🗄️  Resetting database..."

# Drop and recreate schema
docker exec discount_engine_db psql -U postgres -d discount_engine -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "✅ Schema reset complete"
echo ""
echo "🌱 Seeding database with new generic design..."

# Activate virtual environment and run seed script
source .venv/bin/activate
python -m scripts.seed_data

echo ""
echo "✨ Database ready!"
echo ""
echo "📊 Available discount rules:"
echo "   AUTO-APPLY:"
echo "   1. 10% off cart > ₹5000 (max ₹1000) - CART:PERCENTAGE, non-stackable"
echo "   2. ₹500 Loyalty Reward - CART:FLAT, stackable, requires_loyalty"
echo "   3. 5% off 3+ Electronics - CATEGORY:PERCENTAGE, stackable"
echo ""
echo "   COUPONS:"
echo "   4. FLAT500 - ₹500 off cart > ₹2000 - CART:FLAT, stackable"
echo "   5. SAVE20 - 20% off cart > ₹3000 (max ₹800) - CART:PERCENTAGE, non-stackable"
echo "   6. ELEC15 - 15% off Electronics (max ₹600) - CATEGORY:PERCENTAGE, stackable"
echo "   7. VIP1000 - ₹1000 off for loyalty - CART:FLAT, stackable, requires_loyalty"
echo "   8. FASHION300 - ₹300 off cart > ₹1500 - CART:FLAT, stackable"
echo ""
echo "🔐 Test Users:"
echo "   - test@example.com / test123 (CUSTOMER)"
echo "   - admin@pragma.ai / admin123 (ADMIN)"
echo ""
echo "🚀 Start server: uvicorn app.main:app --reload"

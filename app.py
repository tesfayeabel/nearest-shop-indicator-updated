from fastapi import FastAPI, HTTPException, Depends, status, Query
from pydantic import BaseModel
import sqlite3
import math
from passlib.context import CryptContext

app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
def get_db_connection():
    conn = sqlite3.connect('example.db')
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic models for request validation
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Helper function to verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Haversine formula to calculate distance
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Endpoint for user registration
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the username already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        # Hash the password
        hashed_password = hash_password(user.password)

        # Insert the new user into the database
        cursor.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (user.username, hashed_password)
        )
        conn.commit()

        return {"message": "User registered successfully"}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Endpoint for user login
@app.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the user from the database
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (user.username,))
        db_user = cursor.fetchone()

        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Verify the password
        if not verify_password(user.password, db_user['password']):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return {"message": "Login successful", "user_id": db_user['id']}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Endpoint to find shops near a user
@app.get("/shops/nearby")
def find_shops_near_user(
    user_id: int,
    radius_km: float = Query(5.0, description="Search radius in kilometers"),
    search_query: Optional[str] = Query(None, description="Search by shop name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    premium_only: bool = Query(False, description="Show only premium shops"),
    sort_by: str = Query("distance", description="Sort by 'distance' or 'rating'"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(10, description="Results per page")
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch user's location
        cursor.execute('SELECT latitude, longitude FROM users WHERE id = ?', (user_id,))
        user_location = cursor.fetchone()

        if not user_location:
            raise HTTPException(status_code=404, detail=f"No user found with id: {user_id}")

        user_lat, user_lon = user_location['latitude'], user_location['longitude']

        # Base query to fetch shops
        query = '''
            SELECT id, name, category, latitude, longitude, rating, premium
            FROM shops
            WHERE 1=1
        '''
        params = []

        # Add search query filter
        if search_query:
            query += ' AND name LIKE ?'
            params.append(f'%{search_query}%')

        # Add category filter
        if category:
            query += ' AND category = ?'
            params.append(category)

        # Add premium filter
        if premium_only:
            query += ' AND premium = 1'

        # Execute the query
        cursor.execute(query, params)
        shops = cursor.fetchall()

        # Calculate distances and filter shops within the radius
        nearby_shops = []
        for shop in shops:
            shop_lat, shop_lon = shop['latitude'], shop['longitude']
            distance = haversine(user_lat, user_lon, shop_lat, shop_lon)
            if distance <= radius_km:
                nearby_shops.append({
                    'id': shop['id'],
                    'name': shop['name'],
                    'category': shop['category'],
                    'latitude': shop_lat,
                    'longitude': shop_lon,
                    'rating': shop['rating'],
                    'premium': bool(shop['premium']),
                    'distance_km': distance
                })

        # Sorting
        if sort_by == "rating":
            nearby_shops_sorted = sorted(nearby_shops, key=lambda x: x['rating'], reverse=True)
        else:  # Default: sort by distance
            nearby_shops_sorted = sorted(nearby_shops, key=lambda x: x['distance_km'])

        # Pagination
        total_shops = len(nearby_shops_sorted)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_shops = nearby_shops_sorted[start:end]

        return {
            "shops": paginated_shops,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_shops": total_shops,
                "total_pages": (total_shops + per_page - 1) // per_page
            }
        }

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
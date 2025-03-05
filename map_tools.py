from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
from uuid import UUID, uuid4
import json
import random

class City(BaseModel):
    name: UUID = Field(default_factory=uuid4)
    coordinates: List[float]
    interests: List[UUID]
    country: str

class Route(BaseModel):
    city_pair: Tuple[UUID, UUID]  # 使用元组确保顺序一致性
    steps: List[UUID]
    distance: float

def generate_random_lat_lon():
    """生成随机的经纬度坐标
    
    Returns:
        List[float]: 包含纬度(-90到90)和经度(-180到180)的列表
    """
    lat = round(random.uniform(-90, 90), 2)
    lon = round(random.uniform(-180, 180), 2)
    return [lat, lon]

def initial_data():
    """初始化数据并保存到JSON文件"""
    # 生成城市数据
    cities_dict = {"aaa": {}, "bbb": {}}
    all_cities = []
    
    # 为每个国家生成10个城市
    for country in ["aaa", "bbb"]:
        for _ in range(10):
            city = City(
                name=uuid4(),
                coordinates=generate_random_lat_lon(),
                interests=[uuid4() for _ in range(random.randint(1,10))],
                country=country
            )
            cities_dict[country][str(city.name)] = json.loads(city.model_dump_json())  # 直接存储为JSON对象而非字符串
            all_cities.append(city)
    
    # 生成路线数据
    routes_dict = {}
    for i in range(len(all_cities)):
        for j in range(i+1, len(all_cities)):
            city1, city2 = all_cities[i], all_cities[j]
            same_country = city1.country == city2.country
            
            steps_count = random.randint(1, 3) if same_country else random.randint(2, 5)
            distance = random.uniform(0, 100) if same_country else random.uniform(100, 300)
            
            # 确保路线键的一致性 - 使用排序后的UUID
            city_ids = sorted([str(city1.name), str(city2.name)])
            route_key = f"{city_ids[0]}_{city_ids[1]}"
            
            route = Route(
                city_pair=(city1.name, city2.name),  # 使用元组
                steps=[uuid4() for _ in range(steps_count)],
                distance=round(distance, 2)
            )
            
            # 只存储一次路线，避免重复
            routes_dict[route_key] = json.loads(route.model_dump_json())  # 直接存储为JSON对象而非字符串
    
    # 保存数据到JSON文件
    with open('cities.json', 'w') as f:
        json.dump(cities_dict, f, indent=2)
    
    with open('routes.json', 'w') as f:
        json.dump(routes_dict, f, indent=2)

def load_data():
    """从JSON文件加载数据并将其转换为Pydantic对象"""
    try:
        with open('cities.json', 'r') as f:
            cities_dict = json.load(f)
        with open('routes.json', 'r') as f:
            routes_dict = json.load(f)

        # 将JSON对象转换为City和Route对象
        cities = {}
        for country, city_items in cities_dict.items():
            cities[country] = {city_id: City(**city_data) for city_id, city_data in city_items.items()}

        routes = {}
        for route_key, route_data in routes_dict.items():
            city1_id, city2_id = route_key.split("_")
            # 更新路由键格式，确保查询时可以找到对应路线
            routes[route_key] = Route(**route_data)
            # 为便于双向查询，添加反向查询支持
            reverse_key = f"{city2_id}_{city1_id}"
            if reverse_key not in routes:
                routes[reverse_key] = routes[route_key]

        return cities, routes
    except FileNotFoundError:
        initial_data()
        return load_data()

# 用于查找两个城市之间的路线
def find_route(routes, city1_id, city2_id):
    """查找两个城市之间的路线"""
    # 尝试两种可能的键格式
    key1 = f"{city1_id}_{city2_id}"
    key2 = f"{city2_id}_{city1_id}"
    
    if key1 in routes:
        return routes[key1]
    elif key2 in routes:
        return routes[key2]
    else:
        return None

# === aaa国的API ===

def get_distance_between_cities_aaa(city1_id: UUID, city2_id: UUID):
    """获取aaa国家中两个城市之间的距离
    
    Args:
        city1_id (UUID): 第一个城市的ID
        city2_id (UUID): 第二个城市的ID
        
    Returns:
        float或str: 如果两个城市都在aaa国且路线存在，返回距离；否则返回错误信息
    """
    cities, routes = load_data()
    
    # 检查城市是否在aaa国
    if str(city1_id) not in cities["aaa"]:
        return "错误：第一个城市不在aaa国"
    if str(city2_id) not in cities["aaa"]:
        return "错误：第二个城市不在aaa国"
    
    route = find_route(routes, str(city1_id), str(city2_id))
    return route.distance if route else "错误：未找到这两个城市之间的路线"

def get_route_between_cities_aaa(city1_id: UUID, city2_id: UUID):
    """获取aaa国家中两个城市之间的路线信息
    
    Args:
        city1_id (UUID): 第一个城市的ID
        city2_id (UUID): 第二个城市的ID
        
    Returns:
        Route或str: 如果两个城市都在aaa国且路线存在，返回路线对象；否则返回错误信息
    """
    cities, routes = load_data()
    
    # 检查城市是否在aaa国
    if str(city1_id) not in cities["aaa"]:
        return "错误：第一个城市不在aaa国"
    if str(city2_id) not in cities["aaa"]:
        return "错误：第二个城市不在aaa国"
    
    route = find_route(routes, str(city1_id), str(city2_id))
    return route if route else "错误：未找到这两个城市之间的路线"

def get_city_coordinates_aaa(city_id: UUID):
    """获取aaa国家中指定城市的坐标
    
    Args:
        city_id (UUID): 城市的ID
        
    Returns:
        List[float]或str: 如果城市在aaa国，返回坐标；否则返回错误信息
    """
    cities, _ = load_data()
    city_str_id = str(city_id)
    if city_str_id in cities["aaa"]:
        return cities["aaa"][city_str_id].coordinates
    return "错误：在aaa国找不到该城市"

def get_nearby_locations_aaa(city_id: UUID, max_distance: float = 50):
    """获取aaa国家中指定城市附近的所有地点
    
    Args:
        city_id (UUID): 目标城市的ID
        max_distance (float, optional): 最大距离阈值，默认为50
        
    Returns:
        List[City]或str: 如果找到符合条件的城市，返回城市列表；否则返回错误信息
    """
    cities, routes = load_data()
    city_str_id = str(city_id)
    
    if city_str_id not in cities["aaa"]:
        return "错误：在aaa国找不到该城市"
    
    nearby_cities = []
    for route_key, route in routes.items():
        city_ids = route_key.split('_')
        if city_str_id in city_ids and route.distance <= max_distance:
            other_id = city_ids[1] if city_ids[0] == city_str_id else city_ids[0]
            if other_id in cities["aaa"]:
                nearby_cities.append(cities["aaa"][other_id])
    
    return nearby_cities if nearby_cities else "未找到附近地点"

# === bbb国的API ===

def get_distance_between_cities_bbb(city1_id: UUID, city2_id: UUID):
    """获取bbb国家中两个城市之间的距离
    
    Args:
        city1_id (UUID): 第一个城市的ID
        city2_id (UUID): 第二个城市的ID
        
    Returns:
        float或str: 如果两个城市都在bbb国且路线存在，返回距离；否则返回错误信息
    """
    cities, routes = load_data()
    
    if str(city1_id) not in cities["bbb"]:
        return "错误：第一个城市不在bbb国"
    if str(city2_id) not in cities["bbb"]:
        return "错误：第二个城市不在bbb国"
    
    route = find_route(routes, str(city1_id), str(city2_id))
    return route.distance if route else "错误：未找到这两个城市之间的路线"

def get_route_between_cities_bbb(city1_id: UUID, city2_id: UUID):
    """获取bbb国家中两个城市之间的路线信息
    
    Args:
        city1_id (UUID): 第一个城市的ID
        city2_id (UUID): 第二个城市的ID
        
    Returns:
        Route或str: 如果两个城市都在bbb国且路线存在，返回路线对象；否则返回错误信息
    """
    cities, routes = load_data()
    
    # 使用字符串表示的UUID进行字典查找
    city1_str = str(city1_id)
    city2_str = str(city2_id)
    
    # 检查城市是否在bbb国
    if city1_str not in cities["bbb"]:
        return "错误：第一个城市不在bbb国"
    if city2_str not in cities["bbb"]:
        return "错误：第二个城市不在bbb国"
    
    route = find_route(routes, city1_str, city2_str)
    return route if route else "错误：未找到这两个城市之间的路线"

def get_city_coordinates_bbb(city_id: UUID):
    """获取bbb国家中指定城市的坐标
    
    Args:
        city_id (UUID): 城市的ID
        
    Returns:
        List[float]或str: 如果城市在bbb国，返回坐标；否则返回错误信息
    """
    cities, _ = load_data()
    city_str_id = str(city_id)
    if city_str_id in cities["bbb"]:
        return cities["bbb"][city_str_id].coordinates
    return "错误：在bbb国找不到该城市"

def get_nearby_locations_bbb(city_id: UUID, max_distance: float = 50):
    """获取bbb国家中指定城市附近的所有地点
    
    Args:
        city_id (UUID): 目标城市的ID
        max_distance (float, optional): 最大距离阈值，默认为50
        
    Returns:
        List[City]或str: 如果找到符合条件的城市，返回城市列表；否则返回错误信息
    """
    cities, routes = load_data()
    city_str_id = str(city_id)
    
    if city_str_id not in cities["bbb"]:
        return "错误：在bbb国找不到该城市"
    
    nearby_cities = []
    for route_key, route in routes.items():
        city_ids = route_key.split('_')
        if city_str_id in city_ids and route.distance <= max_distance:
            other_id = city_ids[1] if city_ids[0] == city_str_id else city_ids[0]
            if other_id in cities["bbb"]:
                nearby_cities.append(cities["bbb"][other_id])
    
    return nearby_cities if nearby_cities else "未找到附近地点"

# === 跨国API ===

def get_cross_country_distance(city1_id: UUID, city2_id: UUID):
    """获取不同国家的两个城市之间的距离
    
    Args:
        city1_id (UUID): 第一个城市的ID
        city2_id (UUID): 第二个城市的ID
        
    Returns:
        float或str: 如果两个城市在不同国家且路线存在，返回距离；否则返回错误信息
    """
    cities, routes = load_data()
    city1_str = str(city1_id)
    city2_str = str(city2_id)
    
    # 查找城市所属国家
    city1_country = None
    city2_country = None
    
    for country in cities:
        if city1_str in cities[country]:
            city1_country = country
        if city2_str in cities[country]:
            city2_country = country
    
    # 验证条件
    if not city1_country:
        return "错误：找不到第一个城市"
    if not city2_country:
        return "错误：找不到第二个城市"
    if city1_country == city2_country:
        return f"错误：两个城市都在{city1_country}国，请使用本国API"
    
    route = find_route(routes, city1_str, city2_str)
    return route.distance if route else "错误：未找到这两个城市之间的路线"

def get_city_country(city_id: UUID):
    """获取指定城市所属的国家
    
    Args:
        city_id (UUID): 城市的ID
        
    Returns:
        str: 城市所属的国家，或者错误信息
    """
    cities, _ = load_data()
    city_str_id = str(city_id)
    
    for country, country_cities in cities.items():
        if city_str_id in country_cities:
            return country
    
    return "错误：未找到该城市"

# 示例使用
if __name__ == "__main__":
    initial_data()
    cities, routes = load_data()
    print(f"加载了 {sum(len(country_cities) for country_cities in cities.values())} 个城市")
    print(f"加载了 {len(routes)} 条路线")
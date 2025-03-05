from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
import json
import os

# 定义文件路径
ROOMS_FILE = "./room_data.json"
BOOKINGS_FILE = "./booking_records.json"

# 定义房间模型
class Room(BaseModel):
    room_id: str
    capacity: int
    bookings: List[List[str]]  # 预定状态，包含开始和结束时间
    facilities: List[str]       # 房间设施

# 定义预订记录模型
class Booking(BaseModel):
    booking_id: str
    room_id: str
    user_name: str
    start_time: str
    end_time: str
    created_at: str

# 初始化房间数据并写入JSON文件
def initialize_rooms_data():
    """初始化房间数据并写入JSON文件"""
    rooms = {
        "R101": Room(
            room_id="R101",
            capacity=8,
            bookings=[["2023-10-01 09:00", "2023-10-01 10:30"], ["2023-10-01 14:00", "2023-10-01 15:00"]],
            facilities=["Whiteboard", "Projector"]
        ),
        "R102": Room(
            room_id="R102",
            capacity=15,
            bookings=[["2023-10-01 11:00", "2023-10-01 12:30"]],
            facilities=["Whiteboard", "Video Conference", "Teleconference"]
        ),
        "R103": Room(
            room_id="R103",
            capacity=25,
            bookings=[["2023-10-01 13:00", "2023-10-01 16:00"]],
            facilities=["Projector", "Video Conference", "Teleconference", "Whiteboard"]
        ),
        "R104": Room(
            room_id="R104",
            capacity=100,
            bookings=[["2023-10-01 10:00", "2023-10-01 12:00"], ["2023-10-01 15:30", "2023-10-01 17:00"]],
            facilities=["Projector", "Video Conference", "Teleconference", "Whiteboard", "Sound System"]
        ),
        "R105": Room(
            room_id="R105",
            capacity=4,
            bookings=[],
            facilities=["Whiteboard"]
        ),
        "R106": Room(
            room_id="R106",
            capacity=200,
            bookings=[["2023-10-01 09:30", "2023-10-01 11:30"], ["2023-10-01 13:30", "2023-10-01 14:30"]],
            facilities=["Projector"]
        ),
        "R107": Room(
            room_id="R107",
            capacity=20,
            bookings=[["2023-10-01 09:00", "2023-10-01 17:00"]], # 全天预订
            facilities=["Whiteboard", "Projector", "Video Conference"]
        ),
        "R108": Room(
            room_id="R108",
            capacity=30,
            bookings=[],
            facilities=["Whiteboard", "Projector", "Video Conference", "Teleconference"]
        ),
        "R109": Room(
            room_id="R109",
            capacity=6,
            bookings=[["2023-10-01 10:00", "2023-10-01 11:00"], ["2023-10-01 14:00", "2023-10-01 16:00"]],
            facilities=["Whiteboard"]
        ),
        "R110": Room(
            room_id="R110",
            capacity=12,
            bookings=[["2023-10-01 09:00", "2023-10-01 10:00"], ["2023-10-01 11:00", "2023-10-01 12:00"]],
            facilities=["Projector", "Whiteboard"]
        )
    }
    
    # 将房间数据转换为可序列化的字典
    rooms_dict = {room_id: room.model_dump() for room_id, room in rooms.items()}
    
    # 写入JSON文件
    with open(ROOMS_FILE, 'w', encoding="utf-8") as f:
        json.dump(rooms_dict, f, indent=4, ensure_ascii=False)
    
    return rooms_dict

# 初始化预订记录文件
def initialize_bookings_file():
    """初始化预订记录文件"""
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

# 读取房间数据
def load_rooms_data():
    """从JSON文件读取房间数据"""
    if not os.path.exists(ROOMS_FILE):
        return initialize_rooms_data()
    
    with open(ROOMS_FILE, 'r') as f:
        rooms_dict = json.load(f)
    
    # 将字典转换为Room对象
    rooms = {room_id: Room(**room_data) for room_id, room_data in rooms_dict.items()}
    return rooms

# 读取预订记录
def load_bookings():
    """从JSON文件读取预订记录"""
    if not os.path.exists(BOOKINGS_FILE):
        initialize_bookings_file()
        return {}
    
    with open(BOOKINGS_FILE, 'r') as f:
        bookings = json.load(f)
    bookings = {booking_id: Booking(**booking_data) for booking_id, booking_data in bookings.items()}
    
    return bookings

# 保存预订记录
def save_booking(booking: Booking):
    """保存预订记录到JSON文件"""
    bookings = load_bookings()
    
    # 将新的预订记录添加到字典中
    bookings[str(booking.booking_id)] = booking
    bookings_dict = {book_id: book.model_dump() for book_id, book in bookings.items()}

    # 保存到文件
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings_dict, f, indent=4, ensure_ascii=False)

# 查询所有房间状态
def get_all_rooms_status(current_time) -> Dict[str, Dict]:
    """
    查询所有房间的当前预定状态。
    返回一个字典，包含每个房间的ID、未来的预定状态。
    """
    rooms = load_rooms_data()
    status = {}
    for room_id, info in rooms.items():
        status[room_id] = {
            "bookings": [b for b in info.bookings if b[0] > current_time],
        }
    return status

# 查询房间具体信息
def get_room_info(room_id: str) -> Dict:
    """
    查询指定房间的详细信息（不包括预定信息）。
    :param room_id: 房间ID
    :return: 房间的其他属性，若房间不存在则返回None
    """
    rooms = load_rooms_data()
    if room_id in rooms:
        room_info = rooms[room_id].model_dump()  # 转换为字典
        del room_info["bookings"]  # 不返回预定信息
        return room_info
    return "不存在该房间"

def get_available_rooms(start_time: str, end_time: str) -> List[str]:
    """
    查询在指定时间段内可预订的房间。
    :param start_time: 预定开始时间
    :param end_time: 预定结束时间
    :return: 可预订房间的ID列表
    """
    rooms = load_rooms_data()
    available_rooms = []
    
    # 将输入的时间字符串转换为datetime对象
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    
    for room_id, info in rooms.items():
        is_available = True
        for booking in info.bookings:
            # 将预订时间字符串转换为datetime对象
            booking_start = datetime.strptime(booking[0], "%Y-%m-%d %H:%M")
            booking_end = datetime.strptime(booking[1], "%Y-%m-%d %H:%M")
            
            # 检查时间冲突
            if not (end_dt <= booking_start or start_dt >= booking_end):
                is_available = False
                break
        if is_available:
            available_rooms.append(room_id)
    return available_rooms

# 预定房间
def book_room(room_id: str, start_time: str, end_time: str, user_name: str) -> str:
    """
    预定指定房间。
    :param room_id: 房间ID
    :param start_time: 预定开始时间
    :param end_time: 预定结束时间
    :param user_name: 用户名
    :return: 预定成功返回成功信息，失败返回失败信息
    """
    rooms = load_rooms_data()
    if room_id in rooms:
        # 将输入的时间字符串转换为datetime对象
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        
        # 检查时间是否可用
        for booking in rooms[room_id].bookings:
            # 将预订时间字符串转换为datetime对象
            booking_start = datetime.strptime(booking[0], "%Y-%m-%d %H:%M")
            booking_end = datetime.strptime(booking[1], "%Y-%m-%d %H:%M")
            
            # 检查时间冲突
            if not (end_dt <= booking_start or start_dt >= booking_end):
                return "该时间段房间已被预订"
        
        # 创建预订记录
        booking_id = str(uuid4())
        booking = Booking(
            booking_id=booking_id,
            room_id=room_id,
            user_name=user_name,
            start_time=start_time,
            end_time=end_time,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        
        # 保存预订记录
        save_booking(booking)
        
        return f"成功预定房间{room_id}，预订ID: {booking_id}"
    else:
        return "不存在该房间"

# 检查是否完成
def check(conditions):
    bookings = load_bookings()
    rooms = load_rooms_data()
    for booking_id, booking_data in bookings.items():
        results = [c(booking_data) for c in conditions]
        r = all(results)
        if r:
            return 1
    return 0

# 初始化程序时，确保房间数据文件和预订记录文件存在
if __name__ == "__main__":
    # if not os.path.exists(ROOMS_FILE):
    initialize_rooms_data()
    # if not os.path.exists(BOOKINGS_FILE):
    initialize_bookings_file()
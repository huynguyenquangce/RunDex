"""Province -> region mapping used by the `region` filter.

Province names are stored as written in the data (official names, with diacritics).
Provinces missing here are simply not matched by a region filter.
"""

from typing import Literal

Region = Literal["north", "central", "highlands", "south"]

REGIONS: dict[str, list[str]] = {
    "north": [
        "Hà Nội",
        "Hải Phòng",
        "Quảng Ninh",
        "Bắc Ninh",
        "Hưng Yên",
        "Ninh Bình",
        "Thái Nguyên",
        "Phú Thọ",
        "Lào Cai",
        "Sơn La",
        "Hòa Bình",
        "Lai Châu",
        "Điện Biên",
        "Lạng Sơn",
        "Cao Bằng",
        "Tuyên Quang",
        "Hà Giang",
        "Yên Bái",
        "Bắc Giang",
        "Vĩnh Phúc",
        "Hải Dương",
        "Thái Bình",
        "Nam Định",
        "Hà Nam",
    ],
    "central": [
        "Thanh Hóa",
        "Nghệ An",
        "Hà Tĩnh",
        "Quảng Bình",
        "Quảng Trị",
        "Huế",
        "Thừa Thiên Huế",
        "Đà Nẵng",
        "Quảng Nam",
        "Quảng Ngãi",
        "Bình Định",
        "Phú Yên",
        "Khánh Hòa",
        "Ninh Thuận",
        "Bình Thuận",
    ],
    "highlands": ["Kon Tum", "Gia Lai", "Đắk Lắk", "Đắk Nông", "Lâm Đồng"],
    "south": [
        "TP. Hồ Chí Minh",
        "Hồ Chí Minh",
        "Cần Thơ",
        "Đồng Nai",
        "Bà Rịa - Vũng Tàu",
        "Bình Dương",
        "Bình Phước",
        "Tây Ninh",
        "Long An",
        "Tiền Giang",
        "Bến Tre",
        "Vĩnh Long",
        "Trà Vinh",
        "Đồng Tháp",
        "An Giang",
        "Kiên Giang",
        "Hậu Giang",
        "Sóc Trăng",
        "Bạc Liêu",
        "Cà Mau",
    ],
}

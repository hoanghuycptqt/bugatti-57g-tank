# Bugatti Type 57G “Tank” – mô hình 3D dựng từ đầu

[![Bugatti Type 57G Tank – góc 3/4 trước](renders/web/01_hero_front_three_quarter.jpg)](renders/01_hero_front_three_quarter.jpg)

Mô hình 3D chiếc Bugatti Type 57G “Tank” khung 57335 (Simeone Museum ghi là 57G 01). Xe chế tạo năm 1936 và thắng 24 Giờ Le Mans 1937 với Jean-Pierre Wimille và Robert Benoist. Đây là chiếc Tank duy nhất còn tồn tại, hiện trưng bày tại Simeone Foundation Automotive Museum (Philadelphia).

Toàn bộ hình học được dựng bằng code Python trong Blender 5.2, không dùng mô hình 3D tải từ mạng. Ảnh chụp xe thật chỉ dùng để đối chiếu kích thước và đường nét.

## Xem 3D

| | |
|---|---|
| **[Mở trình xem 3D có màu](https://hoanghuycptqt.github.io/bugatti-57g-tank/)** | Xoay, phóng to, chọn nhanh các góc (mũi xe, khoang lái, đuôi xe…). Chạy được trên máy tính và điện thoại. |
| **[Xem 3D ngay trên GitHub](model/57G_Tank.stl)** | Trình xem STL có sẵn của GitHub: bản xem nhanh một màu (~17 nghìn tam giác, 1,9 MB). Bản chi tiết để tải về hoặc in 3D: [`57G_Tank_hd.stl`](model/57G_Tank_hd.stl) (~184 nghìn tam giác, 9,2 MB). |
| **[Tải file Blender đầy đủ](https://github.com/hoanghuycptqt/bugatti-57g-tank/releases/latest)** | `Bugatti_57G_Tank.blend` (67,5 MB) gồm vật liệu, studio và 16 camera. |
| [`model/57G_Tank.glb`](model/57G_Tank.glb) | glTF 2.0 nén Draco, 2,7 MB, khoảng 0,92 triệu tam giác. Dùng được cho web, AR, three.js, Unity, Unreal… |

## Ảnh render

Render bằng Cycles, nền studio trắng. Bấm vào ảnh để xem bản gốc 2400 px.

| | |
|:---:|:---:|
| [![3/4 sau](renders/web/02_hero_rear_three_quarter.jpg)](renders/02_hero_rear_three_quarter.jpg)<br>3/4 sau | [![3/4 trước bên trái](renders/web/04_front_three_quarter_left.jpg)](renders/04_front_three_quarter_left.jpg)<br>3/4 trước bên trái |
| [![Hông phải](renders/web/03_side_right.jpg)](renders/03_side_right.jpg)<br>Hông phải | [![Hông trái](renders/web/07_side_left.jpg)](renders/07_side_left.jpg)<br>Hông trái |
| [![Chính diện trước](renders/web/05_front.jpg)](renders/05_front.jpg)<br>Chính diện trước | [![Chính diện sau](renders/web/06_rear.jpg)](renders/06_rear.jpg)<br>Chính diện sau |
| [![Góc cao](renders/web/08_high_three_quarter.jpg)](renders/08_high_three_quarter.jpg)<br>Góc cao 3/4 | [![Bánh xe](renders/web/13_detail_wheel.jpg)](renders/13_detail_wheel.jpg)<br>Bánh căm 64 nan, trống phanh có vành răng |
| [![Mũi xe](renders/web/09_detail_nose.jpg)](renders/09_detail_nose.jpg)<br>Mũi xe: lưới tản nhiệt móng ngựa, đèn pha có lồng lưới | [![Khoang lái](renders/web/10_detail_cockpit.jpg)](renders/10_detail_cockpit.jpg)<br>Khoang lái: vô-lăng gỗ, táp-lô, đồng hồ |
| [![Đuôi xe](renders/web/11_detail_tail.jpg)](renders/11_detail_tail.jpg)<br>Đuôi xe: bánh dự phòng, đèn hậu, lỗ thoát | [![Đèn phụ](renders/web/12_detail_side_lamp.jpg)](renders/12_detail_side_lamp.jpg)<br>Đèn phụ bên hông phải |
| [![Khớp ảnh bảo tàng 3/4 trước](renders/web/14_match_museum_f3q.jpg)](renders/14_match_museum_f3q.jpg)<br>Cùng góc máy với ảnh bảo tàng (3/4 trước) | [![Khớp ảnh bảo tàng 3/4 sau](renders/web/15_match_museum_r3q.jpg)](renders/15_match_museum_r3q.jpg)<br>Cùng góc máy với ảnh bảo tàng (3/4 sau) |

## Kích thước chính

| Thông số | Giá trị |
|---|---|
| Chiều dài cơ sở | 2,98 m |
| Vệt bánh trước/sau | 1,35 m |
| Dài thân | ~4,75 m (tính cả lồng đèn pha và đèn hậu ~4,80 m) |
| Rộng tổng | ~1,63 m |
| Cao thân (nắp capo) | ~1,05 m |
| Cao tới mép kính chắn gió | ~1,21 m |
| Lốp | 5.25/5.50-19, bán kính ~0,395–0,40 m |

## Độ khớp với xe thật

- Hình bóng nhìn từ hai bên, trước và sau được so từng cột điểm ảnh với ảnh của Simeone. Sai lệch thường 1–3 cm.
- Camera của ảnh 3/4 trước và 3/4 sau được giải ngược bằng PnP từ 10 điểm mốc (tâm bánh, đèn, gương, kính…). Sai số trung bình 6,7 px (3/4 trước) và 3,9 px (3/4 sau) trên ảnh rộng 1200 px.
- Ảnh 14 và 15 ở trên render đúng các góc máy đó, để đặt cạnh ảnh bảo tàng mà so.

## Chi tiết đã dựng

- **Thân xe:** sơn hai màu xanh nhạt và xanh navy; mảng navy chéo ở sườn, vùng lõm bánh dự phòng và chữ V navy dưới đuôi; khe hở tấm vỏ (cửa, mối nối sườn, mép nắp capo), đinh tán, cửa gió dập trên capo.
- **Mũi xe:** lưới tản nhiệt hình móng ngựa bằng lưới đan thật, hốc gió dưới có 2 đèn sương mù, đèn pha có lồng lưới bảo vệ và giá đỡ, 4 ô gió trên mỗi tai trước, dây da khóa nắp capo.
- **Sườn và đuôi:** đèn phụ bên phải nằm trong hốc lõm, nắp xăng đôi, khe gió chéo hai bên sườn, cửa gió đuôi lưới thưa, 4 đèn hậu và 11 lỗ thoát, bánh dự phòng nằm nghiêng trong đuôi, ống xả chạy dưới sườn trái.
- **Khoang lái:** kính chắn gió cong, gương giữa và 2 gương tròn, táp-lô sơn đen nhăn, đồng hồ chữ Pháp, vô-lăng gỗ 4 chấu, ghế bucket da đen, cần số núm ngà, tên hai tay lái Wimille và Benoist trên nắp capo như trên xe thật.
- **Bánh xe:** bánh căm 64 nan, trống phanh nhôm có vành răng, ốc tai thỏ.

## Cách dựng

1. **Thân xe** là một hàm khoảng cách có dấu (SDF) viết bằng numpy: thân, nắp capo và bốn tai xe là các mặt cắt siêu elip thay đổi dọc chiều dài, ghép với nhau bằng phép hợp mềm. Các hốc (lưới tản nhiệt, cửa gió, bánh dự phòng) được khoét bằng phép trừ mềm.
2. Bề mặt được lấy ra bằng marching cubes với ô 5 mm (khoảng 2,2 triệu tam giác), rồi chiếu Newton lên đúng mặt và tính pháp tuyến giải tích.
3. **Màu sơn, khe hở và vùng tối** được tính thành các trường số trên từng đỉnh và đưa vào shader Cycles, nên đường ranh sắc nét mà không cần texture.
4. **Chi tiết** (lưới đan, đèn, bánh căm, khoang lái…) được sinh bằng bmesh trong `scripts/build/`.
5. **Bản web:** thân xe giảm còn khoảng 0,48 triệu tam giác rồi được cắt đúng theo đường ranh màu sơn và khe hở, nên GLB chỉ dùng màu phẳng, không cần texture, và nén Draco còn 2,7 MB. Trang xem 3D tải file này qua jsDelivr cho nhanh. Bản STL xem nhanh là file dạng text, đơn vị mm, giữ dưới 2 MB: GitHub nhúng sẵn file text cỡ này vào trang nên hiển thị được cả khi mạng tới GitHub chậm, còn file nhị phân lớn được tải riêng và có thể báo “Unable to render code block”. Bản HD là file nhị phân (đơn vị mét) với thân xe được chia lưới đều lại cho đẹp khi hiển thị phẳng.

Mô hình được dựng bởi Claude (Anthropic) điều khiển Blender qua MCP. Toàn bộ mã nằm trong `scripts/`; các script ghi đường dẫn tuyệt đối của máy dựng, cần sửa lại trước khi chạy.

## Cấu trúc thư mục

```
index.html            trang xem 3D (GitHub Pages + model-viewer)
model/57G_Tank.glb    mô hình có màu (glTF 2.0, nén Draco)
model/57G_Tank.stl    bản xem nhanh cho trình xem STL của GitHub (text, đơn vị mm)
model/57G_Tank_hd.stl bản STL chi tiết (nhị phân, đơn vị mét), để tải về hoặc in 3D
renders/              15 ảnh render 2400 px và ảnh tổng hợp (bản thu nhỏ cho README ở renders/web/)
scripts/build/        mã dựng thân xe và chi tiết (Python, numpy, scikit-image, bpy)
scripts/blender/      các text block có trong file .blend
scripts/render/       script render nền và danh sách camera
scripts/web/          xuất bản web (GLB, STL)
```

## Render lại

Tải `Bugatti_57G_Tank.blend` ở mục [Releases](https://github.com/hoanghuycptqt/bugatti-57g-tank/releases/latest), đặt vào thư mục gốc của repo rồi chạy:

```
blender -b Bugatti_57G_Tank.blend -P scripts/render/render_final.py -- scripts/render/jobs_final.json
```

Ảnh ra thư mục `renders/out/`. Script chọn GPU Metal (máy Mac); trên máy khác, bước này được bỏ qua và Cycles dùng thiết bị đang cài trong Blender.

## Thương hiệu

Mô hình không có logo hay chữ thương hiệu: không có huy hiệu trên mũi xe, không có chữ trên vành, trên lốp hay trên mặt đồng hồ. Tên “Bugatti” và “Type 57G Tank” chỉ dùng để gọi đúng chiếc xe lịch sử; dự án này không liên quan đến Bugatti.

## Nguồn tham khảo

- Simeone Foundation Automotive Museum – [1936 Bugatti 57G “Tank”](https://simeonemuseum.org/collection/1936-bugatti-57g-tank/). Ảnh © Michael Furman, chỉ dùng để đối chiếu và không có trong repo này.
- Wikipedia – [Bugatti Type 57](https://en.wikipedia.org/wiki/Bugatti_Type_57)
- Classic Driver – [Le Mans-winning Bugatti Tank: first and last, a rare breed](https://www.classicdriver.com/en/article/cars/le-mans-winning-bugatti-tank-first-and-last-a-rare-breed)

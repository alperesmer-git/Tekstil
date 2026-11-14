// Türkçe etiket sözlükleri (veritabanı adları değişmez, yalnızca ekranda görünen metinler)
const TABLES = {
 tenant:'Firmalar', app_user:'Kullanıcılar', unit_of_measure:'Ölçü birimleri', business_partner:'İş ortakları (müşteri / tedarikçi / fason)',
 working_calendar:'Çalışma takvimleri', working_calendar_day:'Takvim günleri', season:'Sezonlar', size_scale:'Beden skalaları', size:'Bedenler',
 color:'Renkler', style:'Modeller', style_variant:'Model varyantları (renk × beden)', material:'Malzemeler', fabric_spec:'Kumaş özellikleri',
 bom:'Ürün ağaçları (BOM)', bom_line:'BOM satırları', department:'Departmanlar', routing:'Rotalar', routing_step:'Rota adımları',
 operation:'Operasyonlar', production_line:'Üretim hatları (bantlar)', machine:'Makineler', operator:'Operatörler', operator_skill:'Operatör becerileri',
 changeover_time:'Model değişim süreleri', sales_order:'Siparişler', order_line:'Sipariş satırları', order_line_qty:'Sipariş renk-beden adetleri',
 purchase_order:'Satın alma siparişleri', purchase_order_line:'Satın alma satırları', material_lot:'Malzeme lotları', stock_movement:'Stok hareketleri',
 material_requirement:'Malzeme ihtiyaçları', marker:'Pastallar', marker_size_ratio:'Pastal beden oranları', cutting_order:'Kesim emirleri',
 subcontract_capacity:'Fason kapasiteleri', subcontract_order:'Fason siparişleri', subcontract_shipment:'Fason sevkiyatları',
 subcontract_shipment_line:'Fason sevkiyat satırları', work_order:'İş emirleri', work_order_variant_qty:'İş emri varyant adetleri',
 production_log:'Üretim kayıtları', downtime_log:'Duruş kayıtları', line_balance:'Hat dengeleme', defect_type:'Hata türleri',
 inspection:'Kalite kontroller', inspection_defect:'Kalite kontrol hataları', plan_scenario:'Plan senaryoları', plan_assignment:'Plan atamaları',
 efficiency_history:'Verimlilik geçmişi', actual_waste_history:'Gerçek fire geçmişi', delivery_prediction:'Termin tahminleri',
 assistant_audit_log:'Asistan denetim kayıtları'
};
const COLS = {
 id:'No', tenant_id:'Firma No', name:'Ad', email:'E-posta', full_name:'Ad Soyad', role:'Rol', is_active:'Aktif mi', code:'Kod',
 is_customer:'Müşteri mi', is_supplier:'Tedarikçi mi', is_subcontractor:'Fason atölye mi', erp_ref:'ERP referansı', calendar_id:'Takvim No',
 day:'Gün', is_working:'Çalışma günü mü', work_minutes:'Çalışma dakikası', size_scale_id:'Beden skalası No', sort_order:'Sıra', season_id:'Sezon No',
 customer_id:'Müşteri No', style_code:'Model kodu', description:'Açıklama', product_group:'Ürün grubu', style_id:'Model No', color_id:'Renk No',
 size_id:'Beden No', sku:'SKU', barcode:'Barkod', material_type:'Malzeme türü', uom:'Birim', material_id:'Malzeme No', composition:'Kompozisyon',
 gsm:'Gramaj (g/m²)', usable_width_cm:'Kullanılabilir en (cm)', shrink_warp_pct:'Çekme – boy (%)', shrink_weft_pct:'Çekme – en (%)',
 yarn_type:'İplik cinsi', knit_or_woven:'Örme / Dokuma', version:'Versiyon', status:'Durum', valid_from:'Geçerlilik başlangıcı', bom_id:'Ürün ağacı No',
 parent_line_id:'Üst satır No', qty_per_unit:'Birim başına miktar', waste_pct:'Fire (%)', applies_color_id:'Geçerli renk No', applies_size_id:'Geçerli beden No',
 usage_note:'Kullanım notu', routing_id:'Rota No', seq:'Sıra', department_id:'Departman No', is_subcontractable:'Fasona verilebilir mi',
 total_smv:'Toplam SMV (dk)', routing_step_id:'Rota adımı No', smv:'SMV (dk)', machine_type:'Makine tipi', required_skill_level:'Gereken beceri seviyesi',
 operator_count:'Operatör sayısı', default_efficiency_pct:'Varsayılan verimlilik (%)', line_id:'Hat No', asset_code:'Demirbaş kodu', home_line_id:'Ana hat No',
 operator_id:'Operatör No', skill_level:'Beceri seviyesi', avg_efficiency_pct:'Ort. verimlilik (%)', from_product_group:'Önceki ürün grubu',
 to_product_group:'Sonraki ürün grubu', minutes:'Süre (dk)', order_no:'Sipariş no', order_date:'Sipariş tarihi', sales_order_id:'Sipariş No',
 ship_date:'Yükleme tarihi', priority:'Öncelik', unit_price:'Birim fiyat', order_line_id:'Sipariş satırı No', variant_id:'Varyant No',
 qty_ordered:'Sipariş adedi', qty_tolerance_pct:'Tolerans (%)', supplier_id:'Tedarikçi No', po_no:'Satın alma no', purchase_order_id:'Satın alma siparişi No',
 qty:'Miktar', promised_date:'Söz verilen tarih', received_date:'Geliş tarihi', lot_no:'Lot no', shade_group:'Ton grubu', roll_count:'Top sayısı',
 qty_received:'Gelen miktar', actual_width_cm:'Gerçek en (cm)', actual_gsm:'Gerçek gramaj (g/m²)', measured_shrink_warp_pct:'Ölçülen çekme – boy (%)',
 measured_shrink_weft_pct:'Ölçülen çekme – en (%)', purchase_order_line_id:'Satın alma satırı No', received_at:'Geliş zamanı', lot_id:'Lot No',
 movement_type:'Hareket türü', ref_table:'Referans tablo', ref_id:'Referans No', moved_at:'Hareket zamanı', net_qty:'Net miktar', gross_qty:'Brüt miktar',
 required_by:'İhtiyaç tarihi', covered_qty:'Karşılanan miktar', fabric_material_id:'Kumaş malzeme No', marker_name:'Pastal adı', length_m:'Boy (m)',
 width_cm:'En (cm)', efficiency_pct:'Verimlilik (%)', source:'Kaynak', marker_id:'Pastal No', pieces:'Parça adedi', planned_plies:'Planlanan kat',
 actual_plies:'Gerçekleşen kat', fabric_used_m:'Kullanılan kumaş (m)', end_loss_m:'Uç firesi (m)', planned_date:'Planlanan tarih',
 subcontractor_id:'Fason atölye No', daily_capacity:'Günlük kapasite', price_per_unit:'Birim fiyat', planned_out_date:'Planlanan çıkış tarihi',
 planned_back_date:'Planlanan dönüş tarihi', subcontract_order_id:'Fason sipariş No', direction:'Yön', waybill_no:'İrsaliye no',
 shipped_at:'Sevk zamanı', shipment_id:'Sevkiyat No', defect_qty:'Hatalı adet', planned_qty:'Planlanan adet', planned_start:'Planlanan başlangıç',
 planned_end:'Planlanan bitiş', actual_start:'Gerçek başlangıç', actual_end:'Gerçek bitiş', work_order_id:'İş emri No', qty_planned:'Planlanan adet',
 client_uuid:'İstemci UUID', qty_good:'Sağlam adet', logged_at:'Kayıt zamanı', synced_at:'Senkron zamanı', reason:'Neden', started_at:'Başlangıç zamanı',
 ended_at:'Bitiş zamanı', station_no:'İstasyon no', operation_id:'Operasyon No', target_per_hour:'Saatlik hedef', category:'Kategori', stage:'Aşama',
 inspected_qty:'Kontrol edilen adet', inspected_at:'Kontrol zamanı', inspector_id:'Kontrolör No', inspection_id:'Kalite kontrol No',
 defect_type_id:'Hata türü No', disposition:'Karar', generated_by:'Üreten', objective_json:'Hedef (JSON)', created_by:'Oluşturan', approved_by:'Onaylayan',
 created_at:'Oluşturma zamanı', scenario_id:'Senaryo No', start_at:'Başlangıç', end_at:'Bitiş', is_locked:'Kilitli mi', produced_qty:'Üretilen adet',
 earned_minutes:'Kazanılan dakika', available_minutes:'Mevcut dakika', planned_waste_pct:'Planlanan fire (%)', actual_waste_pct:'Gerçek fire (%)',
 cutting_order_id:'Kesim emri No', method:'Yöntem', model_version:'Model versiyonu', predicted_finish:'Tahmini bitiş', delay_probability:'Gecikme olasılığı',
 predicted_at:'Tahmin zamanı', actual_finish:'Gerçek bitiş', user_id:'Kullanıcı No', question:'Soru', tool_calls:'Araç çağrıları', answer:'Cevap'
};
const TYPES = {
 integer:'tam sayı', bigint:'tam sayı', smallint:'tam sayı', numeric:'sayı', real:'sayı', 'double precision':'sayı', text:'metin',
 'character varying':'metin', character:'metin', boolean:'evet / hayır', date:'tarih (YYYY-AA-GG)', 'timestamp with time zone':'tarih-saat',
 'timestamp without time zone':'tarih-saat', uuid:'UUID', jsonb:'JSON', json:'JSON'
};
const VALUES = {
 admin:'Yönetici', planner:'Planlamacı', manager:'Üretim müdürü', operator:'Operatör', quality:'Kalite sorumlusu', viewer:'Yalnızca görüntüleyen',
 fabric:'Kumaş', yarn:'İplik', trim:'Yardımcı malzeme (trim)', accessory:'Aksesuar', packaging:'Ambalaj', label:'Etiket',
 knit:'Örme', woven:'Dokuma', draft:'Taslak', approved:'Onaylandı', obsolete:'Geçersiz', open:'Açık', in_production:'Üretimde',
 shipped:'Sevk edildi', closed:'Kapandı', cancelled:'İptal edildi', receipt:'Giriş (mal kabul)', issue_cutting:'Kesime çıkış',
 issue_subcontract:'Fasona çıkış', return:'İade', adjustment:'Düzeltme', out:'Giden (fasona)', in:'Dönen (fasondan)',
 planned:'Planlandı', released:'Serbest bırakıldı', running:'Üretimde', done:'Tamamlandı', blocked:'Engelli',
 machine_breakdown:'Makine arızası', material_wait:'Malzeme bekleme', changeover:'Model değişimi', no_operator:'Operatör yok',
 power:'Elektrik kesintisi', other:'Diğer', sewing:'Dikim', print:'Baskı', wash:'Yıkama', finishing:'Bitim (ütü-paket)', measurement:'Ölçü',
 incoming_fabric:'Gelen kumaş', inline:'Hat içi', endline:'Hat sonu', final:'Final kontrol', subcontract_return:'Fason dönüşü',
 repair:'Tamir', second_quality:'İkinci kalite', scrap:'Hurda', manual:'Manuel', rule_based:'Kural tabanlı', ortools:'OR-Tools',
 proposed:'Önerildi', rejected:'Reddedildi', superseded:'Yerini yenisi aldı', ml:'Makine öğrenmesi'
};
const L = {
 v: n => VALUES[n] || n,
 t: n => TABLES[n] || n,
 c: n => COLS[n] || n,
 ty: n => TYPES[n] || n
};

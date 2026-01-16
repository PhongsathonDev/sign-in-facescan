function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Sheet1"); // ⚠️ ตรวจสอบว่าชื่อ Sheet ของคุณชื่อ "Sheet1" หรือไม่ ถ้าไม่ใช่ให้แก้ตรงนี้
  
  var data = JSON.parse(e.postData.contents);
  
  if (data.length === 0) {
    return ContentService.createTextOutput("No data received");
  }

  // ล็อคป้องกันการแย่งกันเขียนข้อมูล
  var lock = LockService.getScriptLock();
  lock.waitLock(30000); // รอได้สูงสุด 30 วินาที

  try {
    var lastRow = sheet.getLastRow();
    var rowsToAdd = [];

    // วนลูปดูข้อมูลที่ส่งมา
    for (var i = 0; i < data.length; i++) {
      var row = data[i];
      
      // 🔍 เช็คหัวตาราง: 
      // ถ้าใน Sheet มีข้อมูลอยู่แล้ว (lastRow > 0) และแถวที่ส่งมาเป็นหัวตาราง (มีคำว่า "Student ID")
      // ให้ข้ามแถวนั้นไป (จะได้ไม่เกิดหัวตารางซ้ำกลางหน้า)
      if (lastRow > 0 && row[0] == "Student ID") {
        continue;
      }
      
      rowsToAdd.push(row);
    }

    // ถ้ามีข้อมูลเหลือให้บันทึก (ที่ไม่ใช่หัวตารางซ้ำ) ให้บันทึกต่อท้าย
    if (rowsToAdd.length > 0) {
      sheet.getRange(lastRow + 1, 1, rowsToAdd.length, rowsToAdd[0].length).setValues(rowsToAdd);
      return ContentService.createTextOutput("✅ Success: Appended " + rowsToAdd.length + " rows.");
    } else {
      return ContentService.createTextOutput("⚠️ Skipped: Only header received or empty data.");
    }

  } catch (err) {
    return ContentService.createTextOutput("❌ Error: " + err.message);
  } finally {
    lock.releaseLock();
  }
}
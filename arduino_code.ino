
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("Ready to Receive Commands!");
  pinMode(13, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0)
  {
    String str = Serial.readStringUntil('\n');
    Serial.print("Loopback: ");
    Serial.println(str);

    // Check for TM2Arduino App Interface
    int score = -1;
    int indexTM = str.indexOf("<:>");
    if (indexTM != -1)
    {
      String scoreStr = str.substring(indexTM+3, str.length());
      scoreStr.replace("%","");
      score = scoreStr.toInt();
      str = str.substring(0, indexTM);
    }
      
    // Action for Each Class
    if (str == "Class 1")
    {
      // Action for Class 1
      digitalWrite(13, HIGH);
    }
    else if (str == "Class 2")
    {
      // Action for Class 2
      digitalWrite(13, LOW);
    }
    else if ((str == "Class 3") && (score > 90))
    {
      // Action for Class 3
      for (int i = 0; i < 3; i++)
      {
        digitalWrite(13, HIGH);
        delay(500);
        digitalWrite(13, LOW);
        delay(500);
      }
    }

    // Clear All Serial Data in Buffer
    while(Serial.available())
      Serial.read();
  }

}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("Ready to Receive Commands!");
  pinMode(13, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(10, OUTPUT);
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
      String scoreStr = str.substring(indexTM + 3, str.length());
      scoreStr.replace("%", "");
      score = scoreStr.toInt();
      str = str.substring(0, indexTM);
    }
 
    // Action for Each Class
    // NOTE: these strings must match your labels.txt EXACTLY (case and
    // spelling). Your Teachable Machine model's classes are named
    // "Rock", "Paper", "Scissors" - not "Class 1/2/3" - so that's what
    // gets compared here.
    // Each branch resets ALL pins first, so only the pins relevant to the
    // current class stay on - switching classes always clears the old state.
    if (str == "Rock")
    {
      // Action for Rock
      digitalWrite(13, HIGH);
      digitalWrite(9, HIGH);
      digitalWrite(8, LOW);
      digitalWrite(10, LOW);
    }
    else if (str == "Paper")
    {
      // Action for Paper
      digitalWrite(13, LOW);
      digitalWrite(9, LOW);
      digitalWrite(10, HIGH);
      digitalWrite(8, LOW);
    }
    else if (str == "Scissors")
    {
      // Action for Scissors
      // (score gate removed - the Python script isn't sending a confidence
      // value yet, so "score" always stays -1 and this branch would never
      // fire with the check left in. Ask me to add score reporting back
      // into the Python script if you want this gated by confidence again.)
      digitalWrite(9, LOW);
      digitalWrite(10, LOW);
      for (int i = 0; i < 3; i++)
      {
        digitalWrite(13, HIGH);
        digitalWrite(8, HIGH);
        delay(500);
        digitalWrite(13, LOW);
        digitalWrite(8, LOW);
        delay(500);
      }
    }
 
    // Clear All Serial Data in Buffer
    while (Serial.available())
      Serial.read();
  }
}
 
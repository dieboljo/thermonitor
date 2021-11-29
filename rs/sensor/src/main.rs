//! # Sensor
//! 
//! A simple program to access an I2C temperature/humidity sensor
//! and push the data to an AWS DynamoDB table.

use {
    aht20::*,
    chrono::Utc,
    embedded_hal::blocking::delay::DelayMs,
    linux_embedded_hal as hal,
    reqwest::blocking::Client,
    serde::ser::{Serialize, Serializer, SerializeStruct},
    std::{env, process},
};

struct PostData {
    location: String,
    device: String,
    timestamp: i64,
    temperature: f32,
    humidity: f32,
}

impl Serialize for PostData {
    /// Defines how a PostData object is serialized for transmission
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut rgb = serializer.serialize_struct("PostData", 5)?;
        rgb.serialize_field("LocationId", &self.location)?;
        rgb.serialize_field("DeviceId", &self.device)?;
        rgb.serialize_field("EpochTime", &self.timestamp)?;
        rgb.serialize_field("Temperature", &self.temperature)?;
        rgb.serialize_field("Humidity", &self.humidity)?;
        rgb.end()
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let sensor_id = "sensor";
    let endpoint = "https://bko7deq544.execute-api.us-east-2.amazonaws.com/dev/sensors";
    let location = "45203";

    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        println!("usage: {} /dev/i2c-N", args[0]);
        process::exit(1);
    }

    let i2c = hal::I2cdev::new(&args[1]).unwrap();

    let mut dev = Aht20::new(i2c, hal::Delay).unwrap();

    loop {
        let epoch_time: i64 = Utc::now().timestamp();

        let (h, t) = dev.read().unwrap();

        println!(
            "relative humidity={0}%; temperature={1}C",
            h.rh(),
            t.celsius()
        );

        let post_data = PostData {
            location: location.into(),
            device: sensor_id.into(),
            timestamp: epoch_time.into(),
            temperature: t.celsius().into(),
            humidity: h.rh().into(),
        };

        let client = Client::new();
        let res = client.post(endpoint)
            .json(&post_data)
            .header("authorization-token", "allow")
            .send()
            .unwrap();

        if res.status().is_success() {
            println!("success!");
        } else if res.status().is_server_error() {
            println!("server error! Status: {:?}", res.status());
        } else {
            println!("Something else happened. Status: {:?}", res.status());
        }

        hal::Delay.delay_ms(5000u16);
    }
}

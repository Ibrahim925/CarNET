class Car {
    constructor(x, y, width, height, controlType) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.angle = 0;
        this.damaged = false;
        this.speed = 0;
        this.acceleration = 0.2;
        this.maxSpeed = controlType === "DUMMY" ? 2 : 3;
        this.friction = 0.05;

        this.useNetwork = controlType === "AI";

        if (controlType !== "DUMMY") {
            this.sensor = new Sensor(this, 30, 80, 2 * Math.PI);
            this.network = new Network([this.sensor.rayCount, 25, 10, 4]);
        }
        this.controls = new Controls(controlType);
    }

    #move() {
        if (this.controls.forward) {
            this.speed += this.acceleration;
        }

        if (this.controls.back) {
            this.speed -= this.acceleration;
        }

        if (this.speed > this.maxSpeed) {
            this.speed = this.maxSpeed;
        } else if (this.speed < -this.maxSpeed / 2) {
            this.speed = -this.maxSpeed / 2;
        }

        if (this.speed > 0) {
            this.speed -= this.friction;
        } else if (this.speed < 0) {
            this.speed += this.friction;
        }

        if (Math.abs(this.speed) < this.friction) {
            this.speed = 0;
        }

        if (this.speed != 0) {
            const flip = this.speed > 0 ? 1 : -1;

            if (this.controls.right) {
                this.angle -= 0.03 * flip;
            }

            if (this.controls.left) {
                this.angle += 0.03 * flip;
            }
        }

        this.x -= Math.sin(this.angle) * this.speed;
        this.y -= Math.cos(this.angle) * this.speed;
    }

    #assessDamage(roadBorders, traffic) {
        for (let i = 0; i < roadBorders.length; i++) {
            if (polysIntersect(this.polygon, roadBorders[i])) {
                return true;
            }
        }

        for (let i = 0; i < traffic.length; i++) {
            if (polysIntersect(this.polygon, traffic[i].polygon)) {
                return true;
            }
        }

        return false;
    }

    #createPolygon() {
        const points = [];
        const rad = Math.hypot(this.width, this.height) / 2;
        const alpha = Math.atan2(this.width, this.height);

        points.push({
            x: this.x - Math.sin(this.angle - alpha) * rad,
            y: this.y - Math.cos(this.angle - alpha) * rad,
        });
        points.push({
            x: this.x - Math.sin(this.angle + alpha) * rad,
            y: this.y - Math.cos(this.angle + alpha) * rad,
        });
        points.push({
            x: this.x - Math.sin(Math.PI + this.angle - alpha) * rad,
            y: this.y - Math.cos(Math.PI + this.angle - alpha) * rad,
        });
        points.push({
            x: this.x - Math.sin(Math.PI + this.angle + alpha) * rad,
            y: this.y - Math.cos(Math.PI + this.angle + alpha) * rad,
        });
        return points;
    }

    update(roadBorders, traffic) {
        !this.damaged && this.#move();
        this.polygon = this.#createPolygon();
        this.damaged = this.damaged
            ? true
            : this.#assessDamage(roadBorders, traffic);
        if (this.sensor) {
            this.sensor.update(roadBorders, traffic);

            if (this.useNetwork) {
                const offsets = this.sensor.readings.map((reading) =>
                    reading === null ? 0 : 1 - reading.offset
                );
                const outputs = Network.feedForward(offsets, this.network);

                this.controls.forward = outputs[0];
                this.controls.left = outputs[1];
                this.controls.right = outputs[2];
                this.controls.back = outputs[3];
            }
        }
    }

    draw(ctx, colour, drawSensor = false) {
        if (this.damaged) {
            ctx.fillStyle = "grey";
        } else {
            ctx.fillStyle = colour;
        }
        ctx.beginPath();
        ctx.moveTo(this.polygon[0].x, this.polygon[0].y);
        for (let i = 1; i < this.polygon.length; i++) {
            ctx.lineTo(this.polygon[i].x, this.polygon[i].y);
        }
        ctx.fill();

        this.sensor && drawSensor && this.sensor.draw(ctx);
    }
}

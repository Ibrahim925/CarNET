const canvas = document.getElementById("carnet-canvas");
canvas.width = 200;

const ctx = canvas.getContext("2d");
const road = new Road(canvas.width / 2, canvas.width * 0.9);
const cars = generateCars(1000);
const traffic = [
    new Car(road.getLaneCenter(1), -100, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(0), -300, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(2), -300, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(0), -600, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(1), -600, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(2), -800, 30, 50, "DUMMY"),
    new Car(road.getLaneCenter(2), -1000, 30, 50, "DUMMY"),
];

let bestCar = cars[0];
const bestCarNetwork = localStorage.getItem("best-network");
if (bestCarNetwork) {
    for (let i = 0; i < cars.length; i++) {
        cars[i].network = JSON.parse(bestCarNetwork);
        if (i !== 0) {
            Network.mutate(cars[i].network, 0.2);
        }
    }
}

animate();

function save() {
    localStorage.setItem("best-network", JSON.stringify(bestCar.network));
}

function discard() {
    localStorage.removeItem("best-network");
}

function generateCars(N) {
    const cars = [];
    for (let i = 1; i <= N; i++) {
        cars.push(new Car(road.getLaneCenter(1), 100, 30, 50, "AI"));
    }
    return cars;
}

function animate() {
    traffic.forEach((car) => {
        car.update(road.borders, []);
    });
    cars.forEach((car) => car.update(road.borders, traffic));

    canvas.height = window.innerHeight;

    bestCar = cars.reduce((prev, curr) => (curr.y < prev.y ? curr : prev));

    ctx.save();
    ctx.translate(0, -bestCar.y + canvas.height * 0.6);

    road.draw(ctx);

    traffic.forEach((car) => {
        car.draw(ctx, "red");
    });

    ctx.globalAlpha = 0.2;

    cars.forEach(
        (car) =>
            car.x !== bestCar.x && car.y !== bestCar.y && car.draw(ctx, "blue")
    );

    ctx.globalAlpha = 1;

    bestCar.draw(ctx, "blue", true);

    ctx.restore();
    requestAnimationFrame(animate);
}

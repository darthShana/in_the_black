import { Component } from '@angular/core';
// import Chart from 'chart.js';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [],
  templateUrl: './bar-chart.component.html',
  styleUrl: './bar-chart.component.scss'
})
export class BarChartComponent {
  public chart: any;

  ngOnInit(): void {
    this.createChart();
  }

  createChart(){
    this.chart = new Chart("bar-chart", {
      type: 'bar', //this denotes tha type of chart

      data: {// values on X-Axis
        labels: ['2022-05-10', '2022-05-11', '2022-05-12','2022-05-13',
          '2022-05-14', '2022-05-15', '2022-05-16','2022-05-17', ],
        datasets: [
          {
            label: "Sales",
            data: ['467','576', '572', '79', '92',
              '574', '573', '576'],
            backgroundColor: '#4d7298'
          },
          {
            label: "Profit",
            data: ['542', '542', '536', '327', '17',
              '0.00', '538', '541'],
            backgroundColor: '#9dc3c2'
          }
        ]
      },
      options: {
        aspectRatio:2.5,
        plugins: {
          title: {
            display: true,
            text: 'Expense Breakdown'
          }
        },
        scales: {
          x: {
            stacked: true,
          },
        }
      }

    });
  }

}

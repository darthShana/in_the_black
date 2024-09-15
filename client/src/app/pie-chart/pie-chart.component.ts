import {Component, Input} from '@angular/core';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-pie-chart',
  standalone: true,
  imports: [],
  templateUrl: './pie-chart.component.html',
  styleUrl: './pie-chart.component.scss'
})
export class PieChartComponent {
  public chart: any;
  @Input() expenses!: [Record<string, any>];

  ngOnInit(): void {
    this.createChart();
  }

  private backgroundColor = [
    'rgba(77, 114, 152, 1)',
    'rgba(119, 166, 182, 1)',
    'rgba(157, 195, 194, 1)',
    'rgba(138, 195, 103, 1)',
    'rgba(179, 216, 156, 1)',
    'rgba(208, 239, 177, 1)',
  ];

  createChart(){
    this.chart = new Chart("pie-chart", {
      type: 'pie', //this denotes tha type of chart

      data: {// values on X-Axis
        labels: this.expenses.map(obj => obj['display_name']),
        datasets: [{
          label: 'Expenses Breakdown',
          data: this.expenses.map(obj => obj['balance']),
          backgroundColor: this.backgroundColor.slice(0, this.expenses.length),
          hoverOffset: 4
        }],
      },
      options: {
        aspectRatio:2.5,
        plugins: {
          title: {
            display: true,
            text: 'Monthly Expenses'
          }
        }      }

    });
  }

}

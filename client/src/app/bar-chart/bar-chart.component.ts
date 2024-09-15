import {Component, Input} from '@angular/core';
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
  @Input() expenses!: [Record<string, any>];
  private backgroundColor = [
    'rgba(77, 114, 152, 1)',
    'rgba(119, 166, 182, 1)',
    'rgba(157, 195, 194, 1)',
    'rgba(138, 195, 103, 1)',
    'rgba(179, 216, 156, 1)',
    'rgba(208, 239, 177, 1)',
  ];

  ngOnInit(): void {
    this.createChart();
  }

  createChart(){

    const uniqueExpenses = [...new Set(this.expenses.flatMap(map => Object.keys(map['expenses'])))];
    const periods = [...new Set(this.expenses.map(p => p['period']))];
    const colors = new Map(uniqueExpenses.map((key, index) => [key, this.backgroundColor[index]]));
    console.log(`uniqueExpenses: ${uniqueExpenses}`)
    console.log(`periods: ${periods}`)

    let dataset = uniqueExpenses.map(e => {
      return {
        label: e,
        data: periods.map(p => {
          const expensesForPeriod = this.expenses.find(month=>month['period']==p) as Record<string, any>
          console.log(expensesForPeriod)
          return expensesForPeriod && expensesForPeriod['expenses'][e]?expensesForPeriod['expenses'][e]:0
        }),
        backgroundColor: colors.get(e)
      }
    })
    console.log('dataset')
    console.log(dataset)

    this.chart = new Chart("bar-chart", {
      type: 'bar', //this denotes tha type of chart

      data: {// values on X-Axis
        labels: periods,
        datasets: dataset
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

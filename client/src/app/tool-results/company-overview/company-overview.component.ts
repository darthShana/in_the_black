import {Component, Input} from '@angular/core';
import {BarChartComponent} from "../../bar-chart/bar-chart.component";
import {MatIcon} from "@angular/material/icon";
import {PieChartComponent} from "../../pie-chart/pie-chart.component";
import {PercentPipe} from "@angular/common";
import {CommonModule} from "@angular/common";

@Component({
  selector: 'app-company-overview',
  standalone: true,
  imports: [
    BarChartComponent,
    MatIcon,
    PieChartComponent,
    PercentPipe,
    CommonModule
  ],
  templateUrl: './company-overview.component.html',
  styleUrl: './company-overview.component.scss'
})
export class CompanyOverviewComponent {

  @Input() companyOverview!: Record<string, any>;

}

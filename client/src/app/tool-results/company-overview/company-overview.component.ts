import {Component, inject, Input} from '@angular/core';
import {BarChartComponent} from "../../bar-chart/bar-chart.component";
import {MatIcon} from "@angular/material/icon";
import {PieChartComponent} from "../../pie-chart/pie-chart.component";
import {PercentPipe} from "@angular/common";
import {CommonModule} from "@angular/common";
import {
  MatCell,
  MatCellDef, MatColumnDef,
  MatHeaderCell, MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef, MatTable
} from "@angular/material/table";
import {MatIconButton} from "@angular/material/button";
import {AddAssetDialog} from "../end-of-year-reports/end-of-year-reports.component";
import {MatDialog} from "@angular/material/dialog";

@Component({
  selector: 'app-company-overview',
  standalone: true,
  imports: [
    BarChartComponent,
    MatIcon,
    PieChartComponent,
    PercentPipe,
    CommonModule,
    MatCell,
    MatCellDef,
    MatHeaderCell,
    MatHeaderRow,
    MatHeaderRowDef,
    MatIconButton,
    MatRow,
    MatRowDef,
    MatTable,
    MatColumnDef,
    MatHeaderCellDef
  ],
  templateUrl: './company-overview.component.html',
  styleUrl: './company-overview.component.scss'
})
export class CompanyOverviewComponent {

  @Input() companyOverview!: Record<string, any>;
  depreciationDisplayedColumns: Iterable<string> = ['date_purchase', 'asset', 'cost', 'closing_value'];
  readonly dialog = inject(MatDialog);

  openDialog() {
    this.dialog.open(AddAssetDialog);
  }
}

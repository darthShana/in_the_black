import {Component, inject, Input, OnInit} from '@angular/core';
import {
  MatCell,
  MatCellDef, MatColumnDef,
  MatHeaderCell, MatHeaderCellDef,
  MatHeaderRow,
  MatHeaderRowDef,
  MatRow,
  MatRowDef, MatTable
} from "@angular/material/table";
import {MatIcon} from "@angular/material/icon";
import {MatButton, MatButtonModule, MatIconButton} from "@angular/material/button";
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {CdkMenuItem} from "@angular/cdk/menu";
import {MatFormField, MatFormFieldModule, MatSuffix} from "@angular/material/form-field";
import {CommonModule, JsonPipe, NgIf} from "@angular/common";
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogActions,
  MatDialogClose,
  MatDialogContent,
  MatDialogTitle
} from "@angular/material/dialog";
import {MatInput, MatInputModule} from "@angular/material/input";
import {AuthService} from "../../../service/auth.service";
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {AssistantService} from "../../../service/assistant.service";
import {ApiService} from "../../../service/api-service.service";

@Component({
  selector: 'app-insights',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCell,
    MatCellDef,
    MatHeaderCell,
    MatHeaderRow,
    MatHeaderRowDef,
    MatIcon,
    MatIconButton,
    MatRow,
    MatRowDef,
    MatTable,
    MatColumnDef,
    MatHeaderCellDef,
    FormsModule,
    ReactiveFormsModule,
    CdkMenuItem,
    MatSuffix
  ],
  templateUrl: './insights.component.html',
  styleUrl: './insights.component.scss'
})
export class InsightsComponent implements OnInit{

  @Input() insights!: Record<string, any>;
  readonly dialog = inject(MatDialog);

  insightsDisplayedColumns: Iterable<string> = ['period', 'insight'];
  acceptedInsightsDisplayedColumns: Iterable<string> = ['period', 'anomaly', 'reason'];
  displayedColumnsWithActions: string[] = []; // new property

  openDialog(row: Record<string, any>) {
    this.dialog.open(AcceptAnomalyDialog, {
      data: row
    });
  }

  ngOnInit(): void {
    this.displayedColumnsWithActions = [...this.insightsDisplayedColumns, 'actions'];
  }

}

@Component({
  selector: 'accept-anomaly-dialog',
  templateUrl: 'accept-anomaly-dialog.html',
  styleUrl: './insights.component.scss',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule, MatDialogTitle, MatDialogContent, MatFormFieldModule, MatInputModule, MatDialogActions, MatButton, MatDialogClose],
})
export class AcceptAnomalyDialog {
  data = inject(MAT_DIALOG_DATA);

  constructor(private authService: AuthService, private assistantService: AssistantService, private httpClient: HttpClient, private apiService: ApiService) {
  }

  acceptAnomalyFrom = new FormGroup({
    period: new FormControl(this.data['period']),
    reason: new FormControl(this.data['insight']),
    acceptReason: new FormControl('', Validators.required)
  })

  accept() {
    this.authService.getUser().then(user => {
      if(user) {
        const headers = new HttpHeaders({
          'Authorization': `Bearer ${user?.access_token}`
        });
        const payload = {
          accepted_anomaly: {
            period: this.acceptAnomalyFrom.value.period,
            insight: this.acceptAnomalyFrom.value.reason,
            accept_reason: this.acceptAnomalyFrom.value.acceptReason
          }
        };

        this.httpClient.post(`${this.apiService.getApiUrl()}/crud-entity-maintenance`,
          payload,
          { headers: headers, withCredentials: true}
          ).pipe().subscribe({
          next: (response) => {
            console.log("Warning Accepted")
            this.assistantService.stream("User has added a reasoning explaining an anomaly found. Re-fetch a user greeting", false, user).then()
          },
          error: (error) => {
            console.error('Error accepting warning', error)
          }
        })
      }
    })
  }
}

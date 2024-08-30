import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EndOfYearReportsComponent } from './end-of-year-reports.component';

describe('EndOfYearReportsComponent', () => {
  let component: EndOfYearReportsComponent;
  let fixture: ComponentFixture<EndOfYearReportsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EndOfYearReportsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EndOfYearReportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

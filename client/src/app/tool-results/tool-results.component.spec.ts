import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolResultsComponent } from './tool-results.component';

describe('ToolResultsComponent', () => {
  let component: ToolResultsComponent;
  let fixture: ComponentFixture<ToolResultsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ToolResultsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ToolResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Select2Module } from 'ng2-select2';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { PlotOptionsComponent } from './plot-options.component';
import { HttpClientModule } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('PlotOptionsComponent', () => {
  let component: PlotOptionsComponent;
  let fixture: ComponentFixture<PlotOptionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PlotOptionsComponent ],
      imports: [
        Select2Module,
        FormsModule,
        RouterModule.forRoot([]),
        HttpClientModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PlotOptionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ReportsComponent } from './reports.component';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import{ NgSelectModule } from '@ng-select/ng-select';

describe('ReportsComponent', () => {
  let spectator: Spectator<ReportsComponent>;
  const createComponent = createComponentFactory({
    component: ReportsComponent,
    imports: [
      HttpClientModule,
      NgSelectModule,
      FormsModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ProcessDataComponent } from './process-data.component';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

describe('ProcessDataComponent', () => {
  let spectator: Spectator<ProcessDataComponent>;
  const createComponent = createComponentFactory({
    component: ProcessDataComponent,
    imports: [
      RouterModule.forRoot([]),
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

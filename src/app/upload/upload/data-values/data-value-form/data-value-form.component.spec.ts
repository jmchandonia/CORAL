import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Select2Module } from 'ng2-select2';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { ModalModule } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';
import { DataValueFormComponent } from './data-value-form.component';
import { DataValue } from 'src/app/shared/models/brick';

describe('DataValueFormComponent', () => {
  let spectator: Spectator<DataValueFormComponent>;
  const createComponent = createComponentFactory({
    component: DataValueFormComponent,
    imports: [
      Select2Module,
      TooltipModule.forRoot(),
      ModalModule.forRoot(),
      HttpClientModule
    ]
  });

  beforeEach(() => spectator =  createComponent({
    props: {
      dataValue: new DataValue(0, true)
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
